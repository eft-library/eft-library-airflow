"""
hideout 배치 임베딩 - Airflow DAG 태스크용 (level 단위)
- hideout_master_i18n + hideout_level_i18n 기준
- hideout_item_require_i18n, hideout_skill_require_i18n
- hideout_station_require_i18n, hideout_trader_require_i18n
- hideout_bonus_i18n, hideout_crafts_i18n 조인
- bge-m3로 임베딩 생성
- rag_documents 테이블에 upsert

청크 분리:
  - level_id_identifier : 식별용 (은신처명 + 레벨) → chunk_type: identifier
  - level_id            : 기본정보 + 건설 조건 (아이템/스킬/시설/상인)
  - level_id_bonuses    : 레벨업 보너스
  - level_id_crafts     : 제작 레시피
"""

import asyncio
import httpx
import json
import logging
from contextlib import closing
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import Variable

OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
BATCH_SIZE = 10
LANGS = ["ko", "en", "ja"]

log = logging.getLogger(__name__)


# ── 유틸
def get_lang_value(jsonb_field: dict | str | None, lang: str) -> str:
    if not jsonb_field:
        return ""
    if isinstance(jsonb_field, str):
        try:
            jsonb_field = json.loads(jsonb_field)
        except json.JSONDecodeError:
            return ""
    return jsonb_field.get(lang, "") or ""


def parse_jsonb(value) -> list | dict | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None


def fmt_duration(seconds: int | None, lang: str) -> str:
    if not seconds:
        return {"ko": "0분", "en": "0min", "ja": "0分"}[lang]
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if lang == "ko":
        return f"{h}시간 {m}분" if h and m else (f"{h}시간" if h else f"{m}분")
    elif lang == "en":
        return f"{h}h {m}min" if h and m else (f"{h}h" if h else f"{m}min")
    else:
        return f"{h}時間 {m}分" if h and m else (f"{h}時間" if h else f"{m}分")


NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}

LABELS = {
    "ko": {
        "hideout": "은신처",
        "level": "레벨",
        "build_time": "건설 시간",
        "items": "건설 필요 아이템",
        "skills": "필요 스킬",
        "stations": "필요 시설",
        "traders": "필요 상인",
        "bonuses": "레벨업 보너스",
        "crafts": "제작 레시피",
        "inraid": "인레이드",
        "duration": "제작 시간",
        "reward": "결과물",
        "requires": "필요 재료",
        "none": "없음",
        "lv": "레벨",
    },
    "en": {
        "hideout": "Hideout",
        "level": "Level",
        "build_time": "Build Time",
        "items": "Required Items",
        "skills": "Required Skills",
        "stations": "Required Stations",
        "traders": "Required Traders",
        "bonuses": "Level Bonuses",
        "crafts": "Craft Recipes",
        "inraid": "Found in Raid",
        "duration": "Craft Time",
        "reward": "Output",
        "requires": "Materials",
        "none": "None",
        "lv": "Level",
    },
    "ja": {
        "hideout": "隠れ家",
        "level": "レベル",
        "build_time": "建設時間",
        "items": "建設必要アイテム",
        "skills": "必要スキル",
        "stations": "必要施設",
        "traders": "必要商人",
        "bonuses": "レベルアップボーナス",
        "crafts": "クラフトレシピ",
        "inraid": "レイド内発見",
        "duration": "クラフト時間",
        "reward": "生成物",
        "requires": "必要素材",
        "none": "なし",
        "lv": "レベル",
    },
}


# ── content 빌더
def build_identifier_content(master_name: dict, level_num: int, lang: str) -> str:
    lb = LABELS[lang]
    hideout_name_ko = get_lang_value(master_name, "ko")
    hideout_name_en = get_lang_value(master_name, "en")
    hideout_name_ja = get_lang_value(master_name, "ja")
    return f"{lb['hideout']}: {hideout_name_ko} | {hideout_name_en} | {hideout_name_ja}\n{lb['level']}: {level_num}"


def build_main_content(
    master_name: dict,
    level_row: dict,
    items: list,
    skills: list,
    stations: list,
    traders: list,
    lang: str,
) -> str:
    lb = LABELS[lang]
    construction_sec = level_row.get("construction_time") or 0
    hideout_name = get_lang_value(master_name, lang)
    level_num = level_row.get("level", "")

    parts = [
        f"{lb['hideout']}: {hideout_name}",
        f"{lb['level']}: {level_num}",
        f"{lb['build_time']}: {fmt_duration(construction_sec, lang)}",
    ]

    if items:
        lines = []
        for item in items:
            name = get_lang_value(item.get("name"), lang)
            quantity = item.get("quantity") or item.get("count", "")
            inraid = f" ({lb['inraid']})" if item.get("found_in_raid") else ""
            lines.append(f"- {name.strip()} x{quantity}{inraid}")
        parts.append(f"\n[{lb['items']}]\n" + "\n".join(lines))

    if skills:
        lines = [
            f"- {get_lang_value(s.get('name'), lang)} {lb['lv']}{s.get('level', '')}"
            for s in skills
        ]
        parts.append(f"\n[{lb['skills']}]\n" + "\n".join(lines))

    if stations:
        lines = [
            f"- {get_lang_value(st.get('name'), lang)} {lb['lv']}{st.get('level', '')}"
            for st in stations
        ]
        parts.append(f"\n[{lb['stations']}]\n" + "\n".join(lines))

    if traders:
        lines = [
            f"- {get_lang_value(t.get('name'), lang)} {lb['lv']}{t.get('value', '')}"
            for t in traders
        ]
        parts.append(f"\n[{lb['traders']}]\n" + "\n".join(lines))

    return "\n".join(parts).strip()


def build_bonuses_content(
    master_name: dict, level_row: dict, bonuses: list, lang: str
) -> str:
    if not bonuses:
        return ""

    lb = LABELS[lang]
    hideout_name = get_lang_value(master_name, lang)
    level_num = level_row.get("level", "")

    lines = []
    for b in bonuses:
        name = get_lang_value(b.get("name"), lang)
        skill_name = get_lang_value(b.get("skill_name"), lang)
        value = b.get("value")
        val_str = f"{float(value):+.4g}" if value is not None else ""
        line = f"- {name}: {val_str}"
        if skill_name:
            line += f" ({skill_name})"
        lines.append(line)

    return "\n".join(
        [
            f"{lb['hideout']}: {hideout_name}",
            f"{lb['level']}: {level_num}",
            f"\n[{lb['bonuses']}]\n" + "\n".join(lines),
        ]
    ).strip()


def build_crafts_content(
    master_name: dict, level_row: dict, crafts: list, lang: str
) -> str:
    if not crafts:
        return ""

    lb = LABELS[lang]
    nk = NAME_KEY[lang]
    hideout_name = get_lang_value(master_name, lang)
    level_num = level_row.get("level", "")

    craft_parts = []
    for c in crafts:
        craft_name = get_lang_value(c.get("name"), lang)
        quantity = c.get("quantity") or 1
        duration = c.get("duration") or 0
        req_items = parse_jsonb(c.get("req_item")) or []

        lines = [
            f"{lb['reward']}: {craft_name.strip()} x{quantity}",
            f"{lb['duration']}: {fmt_duration(int(duration), lang)}",
        ]
        if req_items:
            req_lines = [
                f"  · {(r.get('item') or {}).get(nk) or (r.get('item') or {}).get('name_en', '')} x{r.get('quantity', '')}"
                for r in req_items
                if r.get("item")
            ]
            lines.append(f"{lb['requires']}:\n" + "\n".join(req_lines))

        craft_parts.append("\n".join(lines))

    return "\n".join(
        [
            f"{lb['hideout']}: {hideout_name}",
            f"{lb['level']}: {level_num}",
            f"\n[{lb['crafts']}]\n" + "\n\n".join(craft_parts),
        ]
    ).strip()


# ── 임베딩
async def get_embedding(client: httpx.AsyncClient, text: str) -> list[float]:
    response = await client.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


# ── upsert (psycopg2 cursor 사용)
def upsert_rag_document(
    cursor,
    source_id: str,
    lang: str,
    content: str,
    embedding: list[float],
    chunk_type: str,
    ref_type: str,
    ref_id: str,
    metadata: dict,
):
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    cursor.execute(
        """
        INSERT INTO rag_documents (
            source_table, source_id, lang,
            content, embedding,
            chunk_type, ref_type, ref_id,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s::vector, %s, %s, %s, %s)
        ON CONFLICT (source_table, source_id, lang, chunk_type)
        DO UPDATE SET
            content    = EXCLUDED.content,
            embedding  = EXCLUDED.embedding,
            ref_type   = EXCLUDED.ref_type,
            ref_id     = EXCLUDED.ref_id,
            metadata   = EXCLUDED.metadata,
            updated_at = NOW()
        """,
        (
            "hideout_level_i18n",
            source_id,
            lang,
            content,
            embedding_str,
            chunk_type,
            ref_type,
            ref_id,
            json.dumps(metadata, ensure_ascii=False),
        ),
    )


# ── 레벨 처리
async def process_level(
    cursor,
    client: httpx.AsyncClient,
    master_row: dict,
    level_row: dict,
    items: list,
    skills: list,
    stations: list,
    traders: list,
    bonuses: list,
    crafts: list,
):
    level_id = level_row["id"]
    master_id = master_row["id"]
    level_num = level_row.get("level", "")
    master_name = master_row["name"]

    base_metadata = {
        "master_id": master_id,
        "level_id": level_id,
        "level": level_num,
        "hideout_name": {
            "ko": get_lang_value(master_name, "ko"),
            "en": get_lang_value(master_name, "en"),
            "ja": get_lang_value(master_name, "ja"),
        },
        "craft_count": len(crafts),
        "url": "https://eftlibrary.com/hideout",
    }

    docs = [
        {
            "source_id": f"{level_id}_identifier",
            "chunk_type": "identifier",
            "build_fn": lambda lang, mn=master_name, ln=level_num: build_identifier_content(
                mn, ln, lang
            ),
            "skip": False,
        },
        {
            "source_id": level_id,
            "chunk_type": "content",
            "build_fn": lambda lang, mn=master_name, lr=level_row, it=items, sk=skills, st=stations, tr=traders: build_main_content(
                mn, lr, it, sk, st, tr, lang
            ),
            "skip": False,
        },
        {
            "source_id": f"{level_id}_bonuses",
            "chunk_type": "content",
            "build_fn": lambda lang, mn=master_name, lr=level_row, bo=bonuses: build_bonuses_content(
                mn, lr, bo, lang
            ),
            "skip": not bonuses,
        },
        {
            "source_id": f"{level_id}_crafts",
            "chunk_type": "content",
            "build_fn": lambda lang, mn=master_name, lr=level_row, cr=crafts: build_crafts_content(
                mn, lr, cr, lang
            ),
            "skip": not crafts,
        },
    ]

    for doc in docs:
        if doc["skip"]:
            continue

        for lang in LANGS:
            content = doc["build_fn"](lang)

            if not content.strip():
                log.warning(f"  ⚠ 빈 content 스킵: {doc['source_id']} [{lang}]")
                continue

            try:
                embedding = await get_embedding(client, content)
                upsert_rag_document(
                    cursor,
                    doc["source_id"],
                    lang,
                    content,
                    embedding,
                    doc["chunk_type"],
                    "hideout",
                    level_id,  # ref_id는 항상 level_id로 통일
                    base_metadata,
                )
                if doc["chunk_type"] == "identifier":
                    lb = LABELS[lang]
                    name = get_lang_value(master_name, lang)
                    upsert_search(cursor, f"{lb['hideout']}: {name}", lang)
                log.info(f"  ✓ {doc['source_id']} [{lang}] 완료")

            except httpx.HTTPError as e:
                log.error(f"  ✗ 임베딩 실패: {doc['source_id']} [{lang}] - {e}")
            except Exception as e:
                log.error(f"  ✗ DB 저장 실패: {doc['source_id']} [{lang}] - {e}")


def _fetch_rows(cursor, query: str, params=None) -> list[dict]:
    """cursor.execute 후 dict 리스트로 반환하는 헬퍼"""
    cursor.execute(query, params or ())
    col_names = [desc[0] for desc in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor.fetchall()]


# ── rag_search_i18n upsert
def upsert_search(cursor, value: str, lang: str):
    if not value.strip():
        return
    cursor.execute(
        """
        INSERT INTO rag_search_i18n (value, lang)
        VALUES (%s, %s)
        ON CONFLICT (value, lang) DO UPDATE SET
            update_time = NOW()
        """,
        (value.strip(), lang),
    )


# ── 메인
async def _run(postgres_conn_id: str):
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            master_rows = _fetch_rows(
                cursor,
                """
                SELECT id, name, level_ids
                FROM hideout_master_i18n
                ORDER BY id ASC
            """,
            )
            log.info(f"총 {len(master_rows)}개 hideout master 로드")

            processed = 0

            async with httpx.AsyncClient() as client:
                for master in master_rows:
                    level_ids = list(master.get("level_ids") or [])
                    master_id = master["id"]
                    master_name_ko = get_lang_value(master["name"], "ko")

                    if not level_ids:
                        continue

                    level_rows = _fetch_rows(
                        cursor,
                        """
                        SELECT id, level, construction_time
                        FROM hideout_level_i18n
                        WHERE id = ANY(%s)
                        ORDER BY level ASC
                    """,
                        (level_ids,),
                    )

                    log.info(
                        f"처리중: {master_name_ko} ({master_id}) | {len(level_rows)}개 레벨"
                    )

                    for level_row in level_rows:
                        level_id = level_row["id"]

                        items = _fetch_rows(
                            cursor,
                            "SELECT name, quantity, count, found_in_raid FROM hideout_item_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        skills = _fetch_rows(
                            cursor,
                            "SELECT name, level FROM hideout_skill_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        stations = _fetch_rows(
                            cursor,
                            "SELECT name, level FROM hideout_station_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        traders = _fetch_rows(
                            cursor,
                            "SELECT name, value FROM hideout_trader_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        bonuses = _fetch_rows(
                            cursor,
                            "SELECT name, skill_name, value FROM hideout_bonus_i18n WHERE level_id = %s ORDER BY type ASC",
                            (level_id,),
                        )
                        crafts = _fetch_rows(
                            cursor,
                            "SELECT name, quantity, duration, req_item FROM hideout_crafts_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )

                        await process_level(
                            cursor,
                            client,
                            master,
                            level_row,
                            items,
                            skills,
                            stations,
                            traders,
                            bonuses,
                            crafts,
                        )
                        processed += 1

        conn.commit()
    log.info(f"=== 완료: {processed}개 레벨 처리 ===")


# ── DAG 진입점
def run_hideout_rag_embed(postgres_conn_id: str = "platform_db"):
    asyncio.run(_run(postgres_conn_id))

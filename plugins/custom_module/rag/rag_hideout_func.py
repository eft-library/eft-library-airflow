import asyncio
import httpx
import json
import logging
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from airflow.sdk import Variable

OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
BATCH_SIZE = 10
LANGS = ["ko", "en", "ja"]

log = logging.getLogger(__name__)


# 유틸
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


def fmt_duration(seconds: int | None) -> str:
    """초 → 시간/분 변환"""
    if not seconds:
        return "0분"
    if seconds < 3600:
        return f"{seconds // 60}분"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}시간 {m}분" if m else f"{h}시간"


def fmt_duration_en(seconds: int | None) -> str:
    if not seconds:
        return "0min"
    if seconds < 3600:
        return f"{seconds // 60}min"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}min" if m else f"{h}h"


def fmt_duration_ja(seconds: int | None) -> str:
    if not seconds:
        return "0分"
    if seconds < 3600:
        return f"{seconds // 60}分"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}時間 {m}分" if m else f"{h}時間"


DURATION_FMT = {
    "ko": fmt_duration,
    "en": fmt_duration_en,
    "ja": fmt_duration_ja,
}

NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}

# 라벨
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


# content 조합
def build_content(
    master_name: dict,
    level_row: dict,
    items: list,
    skills: list,
    stations: list,
    traders: list,
    bonuses: list,
    crafts: list,
    lang: str,
) -> str:
    lb = LABELS[lang]
    nk = NAME_KEY[lang]
    dur_fmt = DURATION_FMT[lang]

    hideout_name = get_lang_value(master_name, lang)
    level_num = level_row.get("level", "")
    construction_sec = level_row.get("construction_time") or 0

    parts = [
        f"{lb['hideout']}: {hideout_name}",
        f"{lb['level']}: {level_num}",
        f"{lb['build_time']}: {dur_fmt(construction_sec)}",
    ]

    # 건설 필요 아이템
    if items:
        lines = []
        for item in items:
            name = get_lang_value(item.get("name"), lang)
            quantity = item.get("quantity") or item.get("count", "")
            inraid = f" ({lb['inraid']})" if item.get("found_in_raid") else ""
            lines.append(f"- {name.strip()} x{quantity}{inraid}")
        parts.append(f"\n[{lb['items']}]\n" + "\n".join(lines))

    # 필요 스킬
    if skills:
        lines = []
        for s in skills:
            name = get_lang_value(s.get("name"), lang)
            level = s.get("level", "")
            lines.append(f"- {name} {lb['lv']}{level}")
        parts.append(f"\n[{lb['skills']}]\n" + "\n".join(lines))

    # 필요 시설
    if stations:
        lines = []
        for st in stations:
            name = get_lang_value(st.get("name"), lang)
            level = st.get("level", "")
            lines.append(f"- {name} {lb['lv']}{level}")
        parts.append(f"\n[{lb['stations']}]\n" + "\n".join(lines))

    # 필요 상인
    if traders:
        lines = []
        for t in traders:
            name = get_lang_value(t.get("name"), lang)
            value = t.get("value", "")
            lines.append(f"- {name} {lb['lv']}{value}")
        parts.append(f"\n[{lb['traders']}]\n" + "\n".join(lines))

    # 레벨업 보너스
    if bonuses:
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
        parts.append(f"\n[{lb['bonuses']}]\n" + "\n".join(lines))

    # 제작 레시피
    if crafts:
        craft_parts = []
        for c in crafts:
            craft_name = get_lang_value(c.get("name"), lang)
            quantity = c.get("quantity") or 1
            duration = c.get("duration") or 0
            req_items = parse_jsonb(c.get("req_item")) or []

            lines = [
                f"{lb['reward']}: {craft_name.strip()} x{quantity}",
                f"{lb['duration']}: {dur_fmt(int(duration))}",
            ]
            if req_items:
                req_lines = []
                for r in req_items:
                    item = r.get("item") or {}
                    item_name = item.get(nk) or item.get("name_en", "")
                    qty = r.get("quantity", "")
                    req_lines.append(f"  · {item_name.strip()} x{qty}")
                lines.append(f"{lb['requires']}:\n" + "\n".join(req_lines))

            craft_parts.append("\n".join(lines))

        parts.append(f"\n[{lb['crafts']}]\n" + "\n\n".join(craft_parts))
    else:
        parts.append(f"\n[{lb['crafts']}]\n{lb['none']}")

    return "\n".join(parts).strip()


async def get_embedding(client: httpx.AsyncClient, text: str) -> list[float]:
    OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
    EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
    response = await client.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["embeddings"][0]


def upsert_rag_document(cursor, source_id, lang, content, embedding, metadata):
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    cursor.execute(
        """
        INSERT INTO rag_documents (source_table, source_id, lang, content, embedding, metadata)
        VALUES (%s, %s, %s, %s, %s::vector, %s)
        ON CONFLICT (source_table, source_id, lang)
        DO UPDATE SET
            content    = EXCLUDED.content,
            embedding  = EXCLUDED.embedding,
            metadata   = EXCLUDED.metadata,
            updated_at = NOW()
        """,
        (
            "hideout_level_i18n",
            source_id,
            lang,
            content,
            embedding_str,
            json.dumps(metadata, ensure_ascii=False),
        ),
    )


def fetch_rows(cursor, query, params=None):
    cursor.execute(query, params or ())
    col_names = [desc[0] for desc in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor.fetchall()]


async def process_level(
    cursor,
    client,
    master_dict,
    level_dict,
    items,
    skills,
    stations,
    traders,
    bonuses,
    crafts,
):
    level_id = level_dict["id"]
    master_id = master_dict["id"]
    level_num = level_dict.get("level", "")
    master_name = master_dict["name"]

    for lang in LANGS:
        content = build_content(
            master_name,
            level_dict,
            items,
            skills,
            stations,
            traders,
            bonuses,
            crafts,
            lang,
        )

        if not content.strip():
            log.warning(f"빈 content 스킵: {level_id} [{lang}]")
            continue

        try:
            embedding = await get_embedding(client, content)
            metadata = {
                "content_type": "joined",
                "source_tables": [
                    "hideout_master_i18n",
                    "hideout_level_i18n",
                    "hideout_item_require_i18n",
                    "hideout_skill_require_i18n",
                    "hideout_station_require_i18n",
                    "hideout_trader_require_i18n",
                    "hideout_bonus_i18n",
                    "hideout_crafts_i18n",
                ],
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
            upsert_rag_document(cursor, level_id, lang, content, embedding, metadata)
            log.info(f"✓ {level_id} [{lang}]")

        except httpx.HTTPError as e:
            log.error(f"✗ 임베딩 실패: {level_id} [{lang}] - {e}")
        except Exception as e:
            log.error(f"✗ DB 저장 실패: {level_id} [{lang}] - {e}")


async def _run(postgres_conn_id: str):
    log.info("=== hideout 배치 임베딩 시작 ===")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            # master 전체 조회
            master_rows = fetch_rows(
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
                    master_name = get_lang_value(master["name"], "ko")

                    if not level_ids:
                        continue

                    # level 조회
                    cursor.execute(
                        """
                        SELECT id, level, construction_time
                        FROM hideout_level_i18n
                        WHERE id = ANY(%s)
                        ORDER BY level ASC
                    """,
                        (level_ids,),
                    )
                    col_names = [desc[0] for desc in cursor.description]
                    level_rows = [
                        dict(zip(col_names, row)) for row in cursor.fetchall()
                    ]

                    log.info(
                        f"처리중: {master_name} ({master['id']}) | {len(level_rows)}개 레벨"
                    )

                    for level_dict in level_rows:
                        level_id = level_dict["id"]

                        # 하위 데이터 조회
                        items = fetch_rows(
                            cursor,
                            "SELECT name, quantity, count, found_in_raid FROM hideout_item_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        skills = fetch_rows(
                            cursor,
                            "SELECT name, level FROM hideout_skill_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        stations = fetch_rows(
                            cursor,
                            "SELECT name, level FROM hideout_station_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        traders = fetch_rows(
                            cursor,
                            "SELECT name, value FROM hideout_trader_require_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )
                        bonuses = fetch_rows(
                            cursor,
                            "SELECT name, skill_name, value FROM hideout_bonus_i18n WHERE level_id = %s ORDER BY type ASC",
                            (level_id,),
                        )
                        crafts = fetch_rows(
                            cursor,
                            "SELECT name, quantity, duration, req_item FROM hideout_crafts_i18n WHERE level_id = %s ORDER BY id ASC",
                            (level_id,),
                        )

                        await process_level(
                            cursor,
                            client,
                            master,
                            level_dict,
                            items,
                            skills,
                            stations,
                            traders,
                            bonuses,
                            crafts,
                        )
                        processed += 1

        conn.commit()
    log.info(f"=== 완료: {processed}개 레벨, {processed * 3}개 row 생성/업데이트 ===")


def run_hideout_rag_embed(postgres_conn_id: str = "tkl_db"):
    asyncio.run(_run(postgres_conn_id))

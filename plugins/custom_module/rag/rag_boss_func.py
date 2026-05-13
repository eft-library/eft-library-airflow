"""
boss_i18n 배치 임베딩 - Airflow DAG 태스크용
- is_boss = true 인 row만 대상
- HTML 파싱 후 텍스트 조합
- bge-m3로 임베딩 생성
- rag_documents 테이블에 upsert

청크 분리:
  - boss_id            : 이름만 (chunk_type: identifier) → RDB 조회용
  - boss_id_main       : 기본정보 + 스폰 위치 + 부위별 체력 (chunk_type: content)
  - boss_id_drops      : 드랍 아이템 (chunk_type: content)
  - boss_id_guide      : 위치 가이드 (chunk_type: content)
"""

import asyncio
import httpx
import json
import logging
from bs4 import BeautifulSoup
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from airflow.sdk import Variable

OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
BATCH_SIZE = 10
LANGS = ["ko", "en", "ja"]

log = logging.getLogger(__name__)


# ── 유틸
SKIP_HEADERS = {"아이콘", "icon", "アイコン"}


def clean_html(html_text: str) -> str:
    """HTML 태그 제거, img 제거, table은 구조화된 텍스트로 변환, 아이콘 컬럼 제거"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")

    for img in soup.find_all("img"):
        img.decompose()

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        headers = []
        skip_indices = set()
        lines = []

        for i, row in enumerate(rows):
            cols = row.find_all(["th", "td"])
            values = [c.get_text(strip=True) for c in cols]

            if i == 0:
                skip_indices = {j for j, h in enumerate(values) if h in SKIP_HEADERS}
                headers = [h for j, h in enumerate(values) if j not in skip_indices]
            else:
                values = [v for j, v in enumerate(values) if j not in skip_indices]
                if headers:
                    line = " | ".join(f"{h}: {v}" for h, v in zip(headers, values))
                else:
                    line = " | ".join(values)
                lines.append(line)

        table.replace_with(soup.new_string("\n" + "\n".join(lines) + "\n"))

    return soup.get_text(separator="\n", strip=True)


def get_lang_value(jsonb_field: dict | str | None, lang: str) -> str:
    """JSONB {ko: '', en: '', ja: ''} 에서 언어별 값 추출"""
    if not jsonb_field:
        return ""
    if isinstance(jsonb_field, str):
        try:
            jsonb_field = json.loads(jsonb_field)
        except json.JSONDecodeError:
            return ""
    return jsonb_field.get(lang, "") or ""


def parse_jsonb(value) -> list | dict | None:
    """JSONB 필드 str/dict/list 모두 처리"""
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


# ── 라벨
LANG_LABELS = {
    "ko": {
        "boss": "보스",
        "faction": "소속",
        "health_total": "총 체력",
        "spawn": "스폰 위치 및 확률",
        "health_detail": "부위별 체력",
        "items": "드랍 아이템",
        "guide": "위치 가이드",
        "order": "순서",
    },
    "en": {
        "boss": "Boss",
        "faction": "Faction",
        "health_total": "Total Health",
        "spawn": "Spawn Locations & Chance",
        "health_detail": "Health by Body Part",
        "items": "Drop Items",
        "guide": "Location Guide",
        "order": "Order",
    },
    "ja": {
        "boss": "ボス",
        "faction": "所属",
        "health_total": "総体力",
        "spawn": "スポーン場所と確率",
        "health_detail": "部位別体力",
        "items": "ドロップアイテム",
        "guide": "場所ガイド",
        "order": "順序",
    },
}

BODY_PART_KEY = {"ko": "bodyPart_ko", "en": "bodyPart_en", "ja": "bodyPart_ja"}
SPAWN_NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}
ITEM_NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}


# ── content 빌더
def build_identifier_content(row: dict, lang: str) -> str:
    """이름만 → RDB 조회용 (chunk_type: identifier)"""
    label = LANG_LABELS[lang]

    name_ko = get_lang_value(row["name"], "ko")
    name_en = get_lang_value(row["name"], "en")
    name_ja = get_lang_value(row["name"], "ja")

    # 스폰 맵 (메타데이터에 있는 spawn_map 활용)
    spawn_map = list(row.get("spawn_map") or [])
    spawn_str = ", ".join(spawn_map) if spawn_map else ""

    content = f"{label['boss']}: {name_ko} | {name_en} | {name_ja}"
    if spawn_str:
        content += f"\n{label['spawn']}: {spawn_str}"

    return content


def build_main_content(row: dict, lang: str) -> str:
    """기본정보 + 스폰 위치 + 부위별 체력 (chunk_type: content)"""
    label = LANG_LABELS[lang]

    name = get_lang_value(row["name"], lang)
    faction = row.get("faction") or ""
    health_total = row.get("health_total") or ""
    order = row.get("order") or ""

    health_detail = parse_jsonb(row.get("health_detail")) or []
    spawn_chance = parse_jsonb(row.get("spawn_chance")) or []

    parts = [f"{label['boss']}: {name}"]
    if order:
        parts.append(f"{label['order']}: {order}")
    if faction:
        parts.append(f"{label['faction']}: {faction}")
    if health_total:
        parts.append(f"{label['health_total']}: {health_total}")

    if spawn_chance:
        lines = []
        for s in spawn_chance:
            name_val = s.get(SPAWN_NAME_KEY[lang]) or s.get("name_en", "")
            chance = s.get("spawnChance", "")
            chance_str = f"{int(float(chance) * 100)}%" if chance != "" else ""
            lines.append(f"- {name_val}: {chance_str}")
        parts.append(f"\n[{label['spawn']}]\n" + "\n".join(lines))

    if health_detail:
        lines = []
        for h in health_detail:
            part = h.get(BODY_PART_KEY[lang]) or h.get("bodyPart_en", "")
            max_hp = h.get("max", "")
            lines.append(f"- {part}: {max_hp}")
        parts.append(f"\n[{label['health_detail']}]\n" + "\n".join(lines))

    return "\n".join(parts).strip()


def build_drops_content(row: dict, lang: str) -> str:
    """드랍 아이템 (chunk_type: content)"""
    label = LANG_LABELS[lang]

    name = get_lang_value(row["name"], lang)
    item_info = parse_jsonb(row.get("item_info")) or []

    if not item_info:
        return ""

    lines = []
    for entry in item_info:
        item = entry.get("item", {})
        item_name = item.get(ITEM_NAME_KEY[lang]) or item.get("name_en", "")
        quantity = entry.get("quantity") or entry.get("count", "")
        lines.append(f"- {item_name.strip()} x{quantity}")

    parts = [
        f"{label['boss']}: {name}",
        f"\n[{label['items']}]\n" + "\n".join(lines),
    ]
    return "\n".join(parts).strip()


def build_guide_content(row: dict, lang: str) -> str:
    """위치 가이드 (chunk_type: content)"""
    label = LANG_LABELS[lang]

    name = get_lang_value(row["name"], lang)
    location_guide = clean_html(get_lang_value(row.get("location_guide"), lang))

    if not location_guide:
        return ""

    parts = [
        f"{label['boss']}: {name}",
        f"\n[{label['guide']}]\n{location_guide}",
    ]
    return "\n".join(parts).strip()


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
            "boss_i18n",
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


# ── 배치 처리
async def _process_batch(cursor, client: httpx.AsyncClient, rows: list[dict]):
    for row in rows:
        boss_id = row["id"]
        item_info = parse_jsonb(row.get("item_info")) or []
        location_guide = get_lang_value(
            row.get("location_guide"), "en"
        )  # 존재 여부 확인용

        base_metadata = {
            "boss_id": boss_id,
            "boss_name": {
                "ko": get_lang_value(row["name"], "ko"),
                "en": get_lang_value(row["name"], "en"),
                "ja": get_lang_value(row["name"], "ja"),
            },
            "url_mapping": row.get("url_mapping") or "",
            "spawn_map": list(row.get("spawn_map") or []),
            "url": f"https://eftlibrary.com/boss/{row.get('url_mapping')}",
        }

        docs = [
            {
                "source_id": boss_id,
                "chunk_type": "identifier",
                "build_fn": lambda lang, r=row: build_identifier_content(r, lang),
                "skip": False,
            },
            {
                "source_id": f"{boss_id}_main",
                "chunk_type": "content",
                "build_fn": lambda lang, r=row: build_main_content(r, lang),
                "skip": False,
            },
            {
                "source_id": f"{boss_id}_drops",
                "chunk_type": "content",
                "build_fn": lambda lang, r=row: build_drops_content(r, lang),
                "skip": not item_info,
            },
            {
                "source_id": f"{boss_id}_guide",
                "chunk_type": "content",
                "build_fn": lambda lang, r=row: build_guide_content(r, lang),
                "skip": not location_guide,
            },
        ]

        for doc in docs:
            if doc["skip"]:
                log.info(f"  - {doc['source_id']} 스킵")
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
                        "boss",
                        boss_id,  # ref_id는 항상 boss_id로 통일
                        base_metadata,
                    )
                    if doc["chunk_type"] == "identifier":
                        lb = LANG_LABELS[lang]
                        name = get_lang_value(row["name"], lang)
                        upsert_search(cursor, f"{lb['boss']}: {name}", lang)
                    log.info(f"  ✓ {doc['source_id']} [{lang}] 완료")

                except httpx.HTTPError as e:
                    log.error(f"  ✗ 임베딩 실패: {doc['source_id']} [{lang}] - {e}")
                except Exception as e:
                    log.error(f"  ✗ DB 저장 실패: {doc['source_id']} [{lang}] - {e}")


async def _run(postgres_conn_id: str, batch_size: int):
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM boss_i18n WHERE is_boss = true")
            total = cursor.fetchone()[0]
            log.info(f"총 {total}개 boss 처리 예정")

            offset = 0
            async with httpx.AsyncClient() as client:
                while offset < total:
                    cursor.execute(
                        """
                        SELECT id, name, faction, health_total, health_detail,
                               item_info, spawn_chance, spawn_map,
                               location_guide, "order", url_mapping
                        FROM boss_i18n
                        WHERE is_boss = true
                        ORDER BY "order" ASC NULLS LAST, id ASC
                        LIMIT %s OFFSET %s
                        """,
                        (batch_size, offset),
                    )
                    rows = cursor.fetchall()
                    if not rows:
                        break

                    col_names = [desc[0] for desc in cursor.description]
                    rows_dict = [dict(zip(col_names, row)) for row in rows]

                    log.info(
                        f"배치: {offset + 1} ~ {offset + len(rows_dict)} / {total}"
                    )
                    await _process_batch(cursor, client, rows_dict)
                    offset += batch_size

        conn.commit()
    log.info("=== 완료 ===")


# DAG 진입점
def run_boss_rag_embed(postgres_conn_id: str = "platform_db", batch_size: int = BATCH_SIZE):
    asyncio.run(_run(postgres_conn_id, batch_size))

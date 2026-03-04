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

SKIP_HEADERS = {"아이콘", "icon", "アイコン"}


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        headers, skip_indices, lines = [], set(), []
        for i, row in enumerate(rows):
            cols = row.find_all(["th", "td"])
            values = [c.get_text(strip=True) for c in cols]
            if i == 0:
                skip_indices = {j for j, h in enumerate(values) if h in SKIP_HEADERS}
                headers = [h for j, h in enumerate(values) if j not in skip_indices]
            else:
                values = [v for j, v in enumerate(values) if j not in skip_indices]
                line = (
                    " | ".join(f"{h}: {v}" for h, v in zip(headers, values))
                    if headers
                    else " | ".join(values)
                )
                lines.append(line)
        table.replace_with(soup.new_string("\n" + "\n".join(lines) + "\n"))
    return soup.get_text(separator="\n", strip=True)


def get_lang_value(jsonb_field, lang: str) -> str:
    if not jsonb_field:
        return ""
    if isinstance(jsonb_field, str):
        try:
            jsonb_field = json.loads(jsonb_field)
        except json.JSONDecodeError:
            return ""
    return jsonb_field.get(lang, "") or ""


LANG_LABELS = {
    "ko": {
        "map": "지도",
        "sub_areas": "구역 목록",
        "extractions": "탈출구 목록",
        "extraction": "탈출구",
        "transits": "트랜짓 목록",
        "transit": "트랜짓",
        "faction": "소속",
        "always_available": "항상 열림",
        "single_use": "1회용",
        "requirements": "요구사항",
        "tip": "팁",
        "yes": "✅",
        "no": "❌",
    },
    "en": {
        "map": "Map",
        "sub_areas": "Sub Areas",
        "extractions": "Extraction Points",
        "extraction": "Extraction",
        "transits": "Transit Points",
        "transit": "Transit",
        "faction": "Faction",
        "always_available": "Always Available",
        "single_use": "Single Use",
        "requirements": "Requirements",
        "tip": "Tip",
        "yes": "✅",
        "no": "❌",
    },
    "ja": {
        "map": "マップ",
        "sub_areas": "エリア一覧",
        "extractions": "脱出ポイント一覧",
        "extraction": "脱出ポイント",
        "transits": "トランジット一覧",
        "transit": "トランジット",
        "faction": "所属",
        "always_available": "常時利用可能",
        "single_use": "一回限り",
        "requirements": "必要条件",
        "tip": "ヒント",
        "yes": "✅",
        "no": "❌",
    },
}


def build_map_content(map_row: dict, sub_areas: list, lang: str) -> str:
    label = LANG_LABELS[lang]
    map_name = get_lang_value(map_row["name"], lang)
    map_name_ko = get_lang_value(map_row["name"], "ko")
    map_name_en = get_lang_value(map_row["name"], "en")
    keywords = {
        "ko": f"{map_name} 맵 지도 기본 정보 구역 {map_name_en}",
        "en": f"{map_name} map basic info areas {map_name_ko}",
        "ja": f"{map_name} マップ 基本情報 エリア {map_name_en}",
    }
    parts = [keywords[lang], f"{label['map']}: {map_name}"]
    if sub_areas:
        lines = [
            f"- {get_lang_value(a['name'], lang)}"
            for a in sub_areas
            if get_lang_value(a["name"], lang)
        ]
        if lines:
            parts.append(f"\n[{label['sub_areas']}]\n" + "\n".join(lines))
    return "\n".join(parts).strip()


def build_extraction_content(map_row: dict, extractions: list, lang: str) -> str:
    label = LANG_LABELS[lang]
    map_name = get_lang_value(map_row["name"], lang)
    map_name_ko = get_lang_value(map_row["name"], "ko")
    map_name_en = get_lang_value(map_row["name"], "en")
    keywords = {
        "ko": f"{map_name} 탈출구 탈출 포인트 출구 {map_name_en}",
        "en": f"{map_name} extraction points exits {map_name_ko}",
        "ja": f"{map_name} 脱出ポイント 出口 {map_name_en}",
    }
    parts = [keywords[lang], f"{label['map']}: {map_name}"]
    ext_parts = []
    for ext in extractions:
        ext_name = get_lang_value(ext["name"], lang)
        faction = ext.get("faction") or ""
        always = label["yes"] if ext.get("always_available") else label["no"]
        single = label["yes"] if ext.get("single_use") else label["no"]
        requirements = clean_html(get_lang_value(ext.get("requirements"), lang))
        tip = clean_html(get_lang_value(ext.get("tip"), lang))
        lines = [f"{label['extraction']}: {ext_name}"]
        if faction:
            lines.append(f"{label['faction']}: {faction}")
        lines.append(f"{label['always_available']}: {always}")
        lines.append(f"{label['single_use']}: {single}")
        if requirements:
            lines.append(f"{label['requirements']}: {requirements}")
        if tip:
            lines.append(f"{label['tip']}: {tip}")
        ext_parts.append("\n".join(lines))
    parts.append(f"\n[{label['extractions']}]\n" + "\n\n".join(ext_parts))
    return "\n".join(parts).strip()


def build_transit_content(map_row: dict, transits: list, lang: str) -> str:
    label = LANG_LABELS[lang]
    map_name = get_lang_value(map_row["name"], lang)
    map_name_ko = get_lang_value(map_row["name"], "ko")
    map_name_en = get_lang_value(map_row["name"], "en")
    keywords = {
        "ko": f"{map_name} 트랜짓 이동 환승 다른 맵 이동 {map_name_en}",
        "en": f"{map_name} transit travel between maps {map_name_ko}",
        "ja": f"{map_name} トランジット マップ間移動 {map_name_en}",
    }
    parts = [keywords[lang], f"{label['map']}: {map_name}"]
    transit_parts = []
    for tr in transits:
        tr_name = get_lang_value(tr["name"], lang)
        faction = tr.get("faction") or ""
        always = label["yes"] if tr.get("always_available") else label["no"]
        single = label["yes"] if tr.get("single_use") else label["no"]
        requirements = clean_html(get_lang_value(tr.get("requirements"), lang))
        tip = clean_html(get_lang_value(tr.get("tip"), lang))
        lines = [f"{label['transit']}: {tr_name}"]
        if faction:
            lines.append(f"{label['faction']}: {faction}")
        lines.append(f"{label['always_available']}: {always}")
        lines.append(f"{label['single_use']}: {single}")
        if requirements:
            lines.append(f"{label['requirements']}: {requirements}")
        if tip:
            lines.append(f"{label['tip']}: {tip}")
        transit_parts.append("\n".join(lines))
    parts.append(f"\n[{label['transits']}]\n" + "\n\n".join(transit_parts))
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
            "map_group_i18n",
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


async def process_map(cursor, client, map_row, sub_areas, extractions, transits):
    map_id = map_row["id"]
    base_metadata = {
        "map_id": map_id,
        "map_name": {
            "ko": get_lang_value(map_row["name"], "ko"),
            "en": get_lang_value(map_row["name"], "en"),
            "ja": get_lang_value(map_row["name"], "ja"),
        },
        "url": f"https://eftlibrary.com/map-of-tarkov/{map_id}",
    }

    docs = [
        {
            "source_id": map_id,
            "content_type": "map_info",
            "source_tables": ["map_group_i18n"],
            "build_fn": lambda lang: build_map_content(map_row, sub_areas, lang),
            "extra": {"sub_area_count": len(sub_areas)},
            "skip": False,
        },
        {
            "source_id": f"{map_id}_extract",
            "content_type": "extraction",
            "source_tables": ["map_group_i18n", "extraction_i18n"],
            "build_fn": lambda lang: build_extraction_content(
                map_row, extractions, lang
            ),
            "extra": {"extraction_count": len(extractions)},
            "skip": not extractions,
        },
        {
            "source_id": f"{map_id}_transit",
            "content_type": "transit",
            "source_tables": ["map_group_i18n", "transit_i18n"],
            "build_fn": lambda lang: build_transit_content(map_row, transits, lang),
            "extra": {"transit_count": len(transits)},
            "skip": not transits,
        },
    ]

    for doc in docs:
        if doc["skip"]:
            continue
        for lang in LANGS:
            content = doc["build_fn"](lang)
            if not content.strip():
                continue
            try:
                embedding = await get_embedding(client, content)
                metadata = {
                    **base_metadata,
                    "content_type": doc["content_type"],
                    "source_tables": doc["source_tables"],
                    **doc["extra"],
                }
                upsert_rag_document(
                    cursor, doc["source_id"], lang, content, embedding, metadata
                )
                log.info(f"✓ {doc['source_id']} [{lang}]")
            except httpx.HTTPError as e:
                log.error(f"✗ 임베딩 실패: {doc['source_id']} [{lang}] - {e}")
            except Exception as e:
                log.error(f"✗ DB 저장 실패: {doc['source_id']} [{lang}] - {e}")


async def _run(postgres_conn_id: str):
    log.info("=== map 배치 임베딩 시작 ===")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            map_rows = fetch_rows(
                cursor,
                """
                SELECT id, name FROM map_group_i18n
                WHERE depth = 1
                ORDER BY id ASC
            """,
            )
            total = len(map_rows)
            log.info(f"총 {total}개 지도 → 최대 {total * 3}개 문서 × 3개 언어")

            async with httpx.AsyncClient() as client:
                for map_row in map_rows:
                    map_id = map_row["id"]

                    sub_areas = fetch_rows(
                        cursor,
                        """
                        SELECT id, name FROM map_group_i18n
                        WHERE parent_value = %s AND depth = 2
                        ORDER BY id ASC
                    """,
                        (map_id,),
                    )

                    extractions = fetch_rows(
                        cursor,
                        """
                        SELECT id, name, faction, always_available, single_use, requirements, tip
                        FROM extraction_i18n
                        WHERE map = %s
                        ORDER BY faction ASC, id ASC
                    """,
                        (map_id,),
                    )

                    transits = fetch_rows(
                        cursor,
                        """
                        SELECT id, name, faction, always_available, single_use, requirements, tip
                        FROM transit_i18n
                        WHERE map = %s
                        ORDER BY faction ASC, id ASC
                    """,
                        (map_id,),
                    )

                    log.info(
                        f"처리중: {map_id} | 구역 {len(sub_areas)}개 | 탈출구 {len(extractions)}개 | 트랜짓 {len(transits)}개"
                    )

                    await process_map(
                        cursor, client, map_row, sub_areas, extractions, transits
                    )

        conn.commit()
    log.info("=== 완료 ===")


def run_map_rag_embed(postgres_conn_id: str = "tkl_db"):
    asyncio.run(_run(postgres_conn_id))

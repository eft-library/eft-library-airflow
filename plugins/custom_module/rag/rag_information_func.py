"""
DYNAMIC_INFO_I18N + INFORMATION_I18N 배치 임베딩 - Airflow DAG 태스크용
- DYNAMIC_INFO_I18N에서 event / patch 타입 추출
- link에서 id 파싱
  event: /event/detail/{id}
  patch: /patch-notes/detail/{id}
- INFORMATION_I18N에서 해당 id 조회 후 조인
- bge-m3로 임베딩 생성
- rag_documents 테이블에 upsert

청크 분리:
  - {item_id}          : 이름만 (chunk_type: identifier) → RDB 조회용
  - {item_id}_content  : 본문 전체 (chunk_type: content)
"""

import asyncio
import httpx
import json
import logging
from bs4 import BeautifulSoup
from contextlib import closing
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import Variable

OLLAMA_BASE_URL = Variable.get("OLLAMA_BASE_URL")
EMBED_MODEL = Variable.get("OLLAMA_EMBED_MODEL")
LANGS = ["ko", "en", "ja"]

log = logging.getLogger(__name__)


# ── 유틸
def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    for tag in soup.find_all(["a", "b", "strong", "em", "i", "span"]):
        tag.unwrap()
    soup = BeautifulSoup(str(soup), "html.parser")
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


# ── 타입 설정
TYPE_CONFIG = {
    "event": {
        "link_prefix": "/event/detail/",
        "db_type": "EVENT",
        "url_prefix": "https://eftlibrary.com/event/detail/",
    },
    "patch": {
        "link_prefix": "/patch-notes/detail/",
        "db_type": "PATCH-NOTES",
        "url_prefix": "https://eftlibrary.com/patch-notes/detail/",
    },
}


def extract_ids_by_type(json_value: dict) -> dict[str, set[str]]:
    """json_value에서 event/patch link 파싱 → { "event": {"event24", ...}, ... }"""
    result = {t: set() for t in TYPE_CONFIG}
    for type_key, cfg in TYPE_CONFIG.items():
        items = json_value.get(type_key, [])
        for item in items:
            link = item.get("link", "")
            if cfg["link_prefix"] in link:
                item_id = link.split(cfg["link_prefix"])[-1].strip("/")
                if item_id:
                    result[type_key].add(item_id)
    return result


# ── 라벨
LANG_LABELS = {
    "ko": {
        "event": "이벤트",
        "patch": "패치 노트",
        "updated": "업데이트",
        "content": "내용",
    },
    "en": {
        "event": "Event",
        "patch": "Patch Note",
        "updated": "Updated",
        "content": "Content",
    },
    "ja": {
        "event": "イベント",
        "patch": "パッチノート",
        "updated": "更新",
        "content": "内容",
    },
}

SEARCH_KEYWORDS = {
    "ko": {
        "event": "이벤트 진행중 현재 이벤트 최신 이벤트",
        "patch": "패치 노트 최신 패치 업데이트 변경사항",
    },
    "en": {
        "event": "event current active latest event",
        "patch": "patch note latest patch update changes",
    },
    "ja": {
        "event": "イベント 現在 最新イベント 開催中",
        "patch": "パッチノート 最新パッチ アップデート 変更点",
    },
}


# ── content 빌더
def build_identifier_content(info_row: dict, type_key: str, lang: str) -> str:
    type_label = LANG_LABELS[lang][type_key]
    name = get_lang_value(info_row["name"], lang)
    return f"{type_label}: {name}"


def build_content(info_row: dict, type_key: str, lang: str) -> str:
    label = LANG_LABELS[lang]
    type_label = label[type_key]
    name = get_lang_value(info_row["name"], lang)
    description = clean_html(get_lang_value(info_row["description"], lang))
    update_time = info_row["update_time"]
    updated_str = update_time.strftime("%Y-%m-%d") if update_time else ""
    keywords = SEARCH_KEYWORDS[lang][type_key]

    parts = [
        f"{keywords} {name}",
        f"{type_label}: {name}",
        f"{label['updated']}: {updated_str}",
    ]
    if description:
        parts.append(f"\n[{label['content']}]\n{description}")

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
            "information_i18n",
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


# ── 타입별 처리
async def _process_type(
    cursor,
    client: httpx.AsyncClient,
    type_key: str,
    ids: set[str],
):
    cfg = TYPE_CONFIG[type_key]
    if not ids:
        log.info(f"[{type_key}] id 없음, 스킵")
        return

    log.info(f"[{type_key}] id 목록: {sorted(ids)}")

    cursor.execute(
        """
        SELECT id, type, name, description, update_time
        FROM information_i18n
        WHERE id = ANY(%s) AND type = %s
        ORDER BY update_time DESC
        """,
        (list(ids), cfg["db_type"]),
    )
    col_names = [desc[0] for desc in cursor.description]
    rows = [dict(zip(col_names, row)) for row in cursor.fetchall()]
    log.info(f"[{type_key}] 조회된 항목: {len(rows)}개")

    for info in rows:
        item_id = info["id"]

        base_metadata = {
            "content_type": type_key,
            "source_tables": ["dynamic_info_i18n", "information_i18n"],
            "item_id": item_id,
            "item_name": {
                "ko": get_lang_value(info["name"], "ko"),
                "en": get_lang_value(info["name"], "en"),
                "ja": get_lang_value(info["name"], "ja"),
            },
            "url": f"{cfg['url_prefix']}{item_id}",
        }

        docs = [
            {
                "source_id": item_id,
                "chunk_type": "identifier",
                "build_fn": lambda lang, r=info, t=type_key: build_identifier_content(
                    r, t, lang
                ),
                "skip": False,
            },
            {
                "source_id": f"{item_id}_content",
                "chunk_type": "content",
                "build_fn": lambda lang, r=info, t=type_key: build_content(r, t, lang),
                "skip": not info.get("description"),
            },
        ]

        for doc in docs:
            if doc["skip"]:
                log.info(f"  - {doc['source_id']} 스킵 (description 없음)")
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
                        type_key,  # ref_type ("event" or "patch")
                        item_id,  # ref_id는 항상 item_id로 통일
                        base_metadata,
                    )
                    log.info(f"  ✓ {doc['source_id']} [{lang}] 완료")

                except httpx.HTTPError as e:
                    log.error(f"  ✗ 임베딩 실패: {doc['source_id']} [{lang}] - {e}")
                except Exception as e:
                    log.error(f"  ✗ DB 저장 실패: {doc['source_id']} [{lang}] - {e}")


# ── 메인
async def _run(postgres_conn_id: str):
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            # 1. DYNAMIC_INFO_I18N 전체 조회
            cursor.execute("SELECT id, json_value FROM dynamic_info_i18n")
            col_names = [desc[0] for desc in cursor.description]
            dynamic_rows = [dict(zip(col_names, row)) for row in cursor.fetchall()]

            # 2. event/patch id 수집
            all_ids: dict[str, set[str]] = {t: set() for t in TYPE_CONFIG}
            for row in dynamic_rows:
                json_value = parse_jsonb(row["json_value"]) or {}
                extracted = extract_ids_by_type(json_value)
                for type_key, ids in extracted.items():
                    all_ids[type_key].update(ids)

            # 3. 타입별 처리
            async with httpx.AsyncClient() as client:
                for type_key, ids in all_ids.items():
                    await _process_type(cursor, client, type_key, ids)

        conn.commit()
    log.info("=== 완료 ===")


# ── DAG 진입점
def run_information_rag_embed(postgres_conn_id: str = "tkl_db"):
    asyncio.run(_run(postgres_conn_id))

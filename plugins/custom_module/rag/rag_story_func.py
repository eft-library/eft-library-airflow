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
    """HTML 태그 제거, img 제거, table은 구조화된 텍스트로 변환, 아이콘 컬럼 제거"""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")

    # img 태그 제거
    for img in soup.find_all("img"):
        img.decompose()

    # table을 구조화된 텍스트로 변환
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        headers = []
        skip_indices = set()
        lines = []

        for i, row in enumerate(rows):
            cols = row.find_all(["th", "td"])
            values = [c.get_text(strip=True) for c in cols]

            if i == 0:
                # 아이콘 컬럼 인덱스 기록 후 헤더에서 제거
                skip_indices = {j for j, h in enumerate(values) if h in SKIP_HEADERS}
                headers = [h for j, h in enumerate(values) if j not in skip_indices]
            else:
                # 아이콘 컬럼 값 제거
                values = [v for j, v in enumerate(values) if j not in skip_indices]
                if headers:
                    line = " | ".join(f"{h}: {v}" for h, v in zip(headers, values))
                else:
                    line = " | ".join(values)
                lines.append(line)

        table.replace_with(soup.new_string("\n" + "\n".join(lines) + "\n"))

    return soup.get_text(separator="\n", strip=True)


def get_lang_value(jsonb_field: dict | str | None, lang: str) -> str:
    """JSONB {ko: '', en: '', ja: ''} 에서 언어별 값 추출 (str/dict 모두 처리)"""
    if not jsonb_field:
        return ""
    # asyncpg가 JSONB를 str로 줄 때 처리
    if isinstance(jsonb_field, str):
        try:
            jsonb_field = json.loads(jsonb_field)
        except json.JSONDecodeError:
            return ""
    return jsonb_field.get(lang, "") or ""


# content 조합
def build_content(row: dict, lang: str) -> str:
    """언어별 임베딩용 텍스트 조합"""
    name = get_lang_value(row["name"], lang)
    objectives = clean_html(get_lang_value(row["objectives"], lang))
    requirements = clean_html(get_lang_value(row["requirements"], lang))
    guide = clean_html(get_lang_value(row["guide"], lang))
    order = row["order"] or ""

    label = {
        "ko": {
            "story": "스토리",
            "order": "순서",
            "objectives": "목표",
            "requirements": "요구사항",
            "guide": "가이드",
        },
        "en": {
            "story": "Story",
            "order": "Order",
            "objectives": "Objectives",
            "requirements": "Requirements",
            "guide": "Guide",
        },
        "ja": {
            "story": "ストーリー",
            "order": "順序",
            "objectives": "目標",
            "requirements": "必要条件",
            "guide": "ガイド",
        },
    }[lang]

    parts = [f"{label['story']}: {name}"]
    if order:
        parts.append(f"{label['order']}: {order}")
    if objectives:
        parts.append(f"\n[{label['objectives']}]\n{objectives}")
    if requirements:
        parts.append(f"\n[{label['requirements']}]\n{requirements}")
    if guide:
        parts.append(f"\n[{label['guide']}]\n{guide}")

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
            "story_i18n",
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


async def _process_batch(cursor, client, rows):
    for row in rows:
        story_id = row["id"]

        for lang in LANGS:
            content = build_content(row, lang)

            if not content.strip():
                log.warning(f"빈 content 스킵: {story_id} [{lang}]")
                continue

            try:
                embedding = await get_embedding(client, content)
                metadata = {
                    "content_type": "single",
                    "source_tables": ["story_i18n"],
                    "story_id": story_id,
                    "story_name": {
                        "ko": get_lang_value(row["name"], "ko"),
                        "en": get_lang_value(row["name"], "en"),
                        "ja": get_lang_value(row["name"], "ja"),
                    },
                    "order": row["order"],
                    "url": f"https://eftlibrary.com/story/{story_id}",
                }
                upsert_rag_document(
                    cursor, story_id, lang, content, embedding, metadata
                )
                log.info(f"✓ {story_id} [{lang}]")

            except httpx.HTTPError as e:
                log.error(f"✗ 임베딩 실패: {story_id} [{lang}] - {e}")
            except Exception as e:
                log.error(f"✗ DB 저장 실패: {story_id} [{lang}] - {e}")


async def _run(postgres_conn_id: str, batch_size: int):
    log.info("=== story_i18n 배치 임베딩 시작 ===")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            cursor.execute("SELECT COUNT(*) FROM story_i18n WHERE id != 'roadmap'")
            total = cursor.fetchone()[0]
            log.info(f"총 {total}개 story 처리 예정")

            offset = 0
            processed = 0

            async with httpx.AsyncClient() as client:
                while offset < total:
                    rows = fetch_rows(
                        cursor,
                        """
                        SELECT id, name, objectives, requirements, guide, "order"
                        FROM story_i18n
                        WHERE id != 'roadmap'
                        ORDER BY "order" ASC NULLS LAST, id ASC
                        LIMIT %s OFFSET %s
                    """,
                        (batch_size, offset),
                    )

                    if not rows:
                        break

                    log.info(f"배치: {offset + 1} ~ {offset + len(rows)} / {total}")
                    await _process_batch(cursor, client, rows)

                    processed += len(rows)
                    offset += batch_size

        conn.commit()
    log.info(f"=== 완료: {processed}개 story, {processed * 3}개 row 생성/업데이트 ===")


def run_story_rag_embed(postgres_conn_id: str = "tkl_db", batch_size: int = 10):
    asyncio.run(_run(postgres_conn_id, batch_size))

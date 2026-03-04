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


def clean_html(html_text: str) -> str:
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    for img in soup.find_all("img"):
        img.decompose()
    return soup.get_text(separator="\n", strip=True)


def yn(value: bool | None, lang: str) -> str:
    yes = {"ko": "✅", "en": "✅", "ja": "✅"}
    no = {"ko": "❌", "en": "❌", "ja": "❌"}
    return yes[lang] if value else no[lang]


# 라벨
LABELS = {
    "ko": {
        "quest": "퀘스트",
        "trader": "상인",
        "min_level": "최소 레벨",
        "kappa": "카파",
        "lightkeeper": "라이트키퍼",
        "prev_quest": "선행 퀘스트",
        "next_quest": "후행 퀘스트",
        "objectives": "목표",
        "rewards": "보상",
        "guide": "가이드",
        "standing": "평판",
    },
    "en": {
        "quest": "Quest",
        "trader": "Trader",
        "min_level": "Min Level",
        "kappa": "Kappa",
        "lightkeeper": "Lightkeeper",
        "prev_quest": "Required Quests",
        "next_quest": "Next Quests",
        "objectives": "Objectives",
        "rewards": "Rewards",
        "guide": "Guide",
        "standing": "Standing",
    },
    "ja": {
        "quest": "クエスト",
        "trader": "商人",
        "min_level": "最低レベル",
        "kappa": "カッパ",
        "lightkeeper": "ライトキーパー",
        "prev_quest": "前提クエスト",
        "next_quest": "次のクエスト",
        "objectives": "目標",
        "rewards": "報酬",
        "guide": "ガイド",
        "standing": "評判",
    },
}

NAME_KEY = {"ko": "name_ko", "en": "name_en", "ja": "name_ja"}


# content 조합
def build_content(quest: dict, npc_name: str, lang: str) -> str:
    lb = LABELS[lang]
    nk = NAME_KEY[lang]

    quest_name = get_lang_value(quest["name"], lang)
    min_level = quest.get("min_player_level") or ""
    kappa = yn(quest.get("kappa_required"), lang)
    lightkeeper = yn(quest.get("lightkeeper_required"), lang)

    task_reqs = parse_jsonb(quest.get("task_requirements")) or []
    task_next = parse_jsonb(quest.get("task_next")) or []
    objectives = parse_jsonb(quest.get("objectives")) or []
    rewards_raw = parse_jsonb(quest.get("finish_rewards")) or {}
    guide_html = get_lang_value(quest.get("guide"), lang)
    guide = clean_html(guide_html)

    parts = [
        f"{lb['quest']}: {quest_name}",
        f"{lb['trader']}: {npc_name}",
    ]
    if min_level:
        parts.append(f"{lb['min_level']}: {min_level}")
    parts.append(f"{lb['kappa']}: {kappa}")
    parts.append(f"{lb['lightkeeper']}: {lightkeeper}")

    # 선행 퀘스트
    if task_reqs:
        lines = [
            f"- {t.get('task', {}).get(nk) or t.get('task', {}).get('name_en', '')}"
            for t in task_reqs
        ]
        parts.append(f"\n[{lb['prev_quest']}]\n" + "\n".join(lines))
    # 후행 퀘스트
    if task_next:
        lines = [
            f"- {t.get('task', {}).get(nk) or t.get('task', {}).get('name_en', '')}"
            for t in task_next
        ]
        parts.append(f"\n[{lb['next_quest']}]\n" + "\n".join(lines))

    # 목표
    if objectives:
        lines = []
        for obj in objectives:
            desc_key = f"description_{lang}"
            desc = obj.get(desc_key, "")
            count = obj.get("count")
            items = obj.get("items") or []

            line = f"- {desc}"
            if count and count > 1:
                line += f" ({count}개)" if lang == "ko" else f" (x{count})"
            if items:
                item_names = ", ".join(i.get(nk) or i.get("name_en", "") for i in items)
                line += f" [{item_names}]"
            lines.append(line)
        parts.append(f"\n[{lb['objectives']}]\n" + "\n".join(lines))

    # 보상
    reward_lines = []
    reward_items = rewards_raw.get("items") or []
    for r in reward_items:
        item = r.get("item") or {}
        item_name = item.get(nk) or item.get("name_en", "")
        quantity = r.get("quantity") or r.get("count", "")
        reward_lines.append(f"- {item_name.strip()} x{quantity}")

    trader_standings = rewards_raw.get("traderStanding") or []
    for ts in trader_standings:
        trader = ts.get("trader") or {}
        trader_name = get_lang_value(
            trader.get("name")
            or {
                "ko": trader.get("name_ko", ""),
                "en": trader.get("name_en", ""),
                "ja": trader.get("name_ja", ""),
            },
            lang,
        ) or trader.get("name_en", "")
        standing = ts.get("standing", "")
        reward_lines.append(f"- {trader_name} {lb['standing']} +{standing}")

    if reward_lines:
        parts.append(f"\n[{lb['rewards']}]\n" + "\n".join(reward_lines))

    # 가이드
    if guide:
        parts.append(f"\n[{lb['guide']}]\n{guide}")

    return "\n".join(parts).strip()


# 임베딩 생성
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
            "quest_i18n",
            source_id,
            lang,
            content,
            embedding_str,
            json.dumps(metadata, ensure_ascii=False),
        ),
    )


async def _process_batch(cursor, client, rows, npc_map):
    for quest in rows:
        quest_id = quest["id"]
        npc_id = quest.get("npc_id") or ""
        npc_names = npc_map.get(npc_id, {"ko": "", "en": "", "ja": ""})

        for lang in LANGS:
            npc_name = npc_names.get(lang, "")
            content = build_content(quest, npc_name, lang)

            if not content.strip():
                log.warning(f"빈 content 스킵: {quest_id} [{lang}]")
                continue

            try:
                embedding = await get_embedding(client, content)
                metadata = {
                    "content_type": "joined",
                    "source_tables": ["quest_i18n", "npc_i18n"],
                    "quest_id": quest_id,
                    "quest_name": {
                        "ko": get_lang_value(quest["name"], "ko"),
                        "en": get_lang_value(quest["name"], "en"),
                        "ja": get_lang_value(quest["name"], "ja"),
                    },
                    "npc_id": npc_id,
                    "npc_name": npc_names,
                    "kappa_required": quest.get("kappa_required") or False,
                    "lightkeeper_required": quest.get("lightkeeper_required") or False,
                    "min_player_level": quest.get("min_player_level"),
                    "url": f"https://eftlibrary.com/quest/detail/{quest.get('url_mapping') or quest_id}",
                }
                upsert_rag_document(
                    cursor, quest_id, lang, content, embedding, metadata
                )
                log.info(f"✓ {quest_id} [{lang}]")

            except httpx.HTTPError as e:
                log.error(f"✗ 임베딩 실패: {quest_id} [{lang}] - {e}")
            except Exception as e:
                log.error(f"✗ DB 저장 실패: {quest_id} [{lang}] - {e}")


async def _run(postgres_conn_id: str, batch_size: int):
    log.info("=== quest_i18n 배치 임베딩 시작 ===")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:

            # npc_map 로드
            cursor.execute(
                """
                SELECT id, name FROM npc_i18n
                WHERE "order" IS NOT NULL
            """
            )
            col_names = [desc[0] for desc in cursor.description]
            npc_rows = [dict(zip(col_names, row)) for row in cursor.fetchall()]
            npc_map = {
                r["id"]: {
                    "ko": get_lang_value(r["name"], "ko"),
                    "en": get_lang_value(r["name"], "en"),
                    "ja": get_lang_value(r["name"], "ja"),
                }
                for r in npc_rows
            }
            log.info(f"NPC 로드 완료: {len(npc_map)}개")

            # 전체 카운트
            cursor.execute("SELECT COUNT(*) FROM quest_i18n")
            total = cursor.fetchone()[0]
            log.info(f"총 {total}개 퀘스트 처리 예정")

            offset = 0
            async with httpx.AsyncClient() as client:
                while offset < total:
                    cursor.execute(
                        """
                        SELECT id, url_mapping, name, npc_id,
                               lightkeeper_required, kappa_required,
                               task_requirements, task_next,
                               objectives, finish_rewards,
                               min_player_level, guide
                        FROM quest_i18n
                        ORDER BY "order" ASC NULLS LAST, id ASC
                        LIMIT %s OFFSET %s
                        """,
                        (batch_size, offset),
                    )
                    col_names = [desc[0] for desc in cursor.description]
                    rows = [dict(zip(col_names, row)) for row in cursor.fetchall()]

                    if not rows:
                        break

                    log.info(f"배치: {offset + 1} ~ {offset + len(rows)} / {total}")
                    await _process_batch(cursor, client, rows, npc_map)
                    offset += batch_size

        conn.commit()
    log.info("=== 완료 ===")


def run_quest_rag_embed(postgres_conn_id: str = "tkl_db", batch_size: int = 10):
    asyncio.run(_run(postgres_conn_id, batch_size))

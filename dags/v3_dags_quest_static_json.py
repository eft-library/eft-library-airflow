import json
import os
import time
from contextlib import closing
from pathlib import Path
from urllib.parse import quote

import pendulum
import requests
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

API_BASE_URL = "https://back.eftlibrary.com/api"
OUTPUT_DIR = Path("/opt/airflow/next-public")
PUBLIC_BASE_PATH = "/static/quest"
REQUEST_TIMEOUT = 60


def _safe_filename(value):
    return quote(str(value), safe="-_.")


def _fetch_json(path):
    url = f"{API_BASE_URL}{path}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != 200:
        raise ValueError(f"Unexpected API status from {url}: {payload.get('status')}")
    if payload.get("data") is None:
        raise ValueError(f"Empty API data from {url}")

    return payload


def _write_json_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")

    with open(tmp_path, "r", encoding="utf-8") as f:
        json.load(f)

    os.replace(tmp_path, path)


def _fetch_targets(postgres_conn_id):
    print("[quest-static] fetch targets from database")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                select normalized_name
                from quests
                where is_use is true
                  and normalized_name is not null
                order by sort_order, name_en, normalized_name;
                """
            )
            quests = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                select normalized_name
                from traders
                where normalized_name is not null
                order by name_en, normalized_name;
                """
            )
            traders = [row[0] for row in cursor.fetchall()]

    print(
        "[quest-static] targets fetched: "
        f"quests={len(quests)}, traders={len(traders)}"
    )
    return {"quests": quests, "traders": traders}


def generate_quest_static_json(postgres_conn_id):
    started_at = time.monotonic()
    targets = _fetch_targets(postgres_conn_id)
    root = OUTPUT_DIR / "static" / "quest" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()
    files = {"details": [], "list_with_trader": []}

    print(f"[quest-static] output root: {root}")

    print("[quest-static] all: start")
    item_started_at = time.monotonic()
    all_payload = _fetch_json("/quest/v3/all")
    _write_json_atomic(root / "all.json", all_payload)
    print(
        "[quest-static] all: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    print("[quest-static] feed: start")
    item_started_at = time.monotonic()
    feed_payload = _fetch_json("/quest/v3/feed")
    _write_json_atomic(root / "feed.json", feed_payload)
    print(
        "[quest-static] feed: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    print("[quest-static] completion graph: start")
    item_started_at = time.monotonic()
    completion_graph = _fetch_json("/quest/v3/completion-graph")
    _write_json_atomic(root / "completion-graph.json", completion_graph)
    print(
        "[quest-static] completion graph: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    for index, normalized_name in enumerate(targets["quests"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[quest-static] details {index}/{len(targets['quests'])}: "
            f"{normalized_name}"
        )
        payload = _fetch_json(f"/quest/v3/detail/{quote(normalized_name, safe='')}")
        filename = f"{_safe_filename(normalized_name)}.json"
        _write_json_atomic(root / "details" / filename, payload)
        files["details"].append(
            {
                "id": normalized_name,
                "path": f"{PUBLIC_BASE_PATH}/v3/details/{filename}",
            }
        )
        print(
            f"[quest-static] details {index}/{len(targets['quests'])} done: "
            f"{normalized_name} ({time.monotonic() - item_started_at:.2f}s)"
        )

    for index, trader_name in enumerate(targets["traders"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[quest-static] list-with-trader {index}/{len(targets['traders'])}: "
            f"{trader_name}"
        )
        payload = _fetch_json(
            f"/quest/v3/list-with-trader/{quote(trader_name, safe='')}"
        )
        filename = f"{_safe_filename(trader_name)}.json"
        _write_json_atomic(root / "list-with-trader" / filename, payload)
        files["list_with_trader"].append(
            {
                "id": trader_name,
                "path": f"{PUBLIC_BASE_PATH}/v3/list-with-trader/{filename}",
            }
        )
        print(
            f"[quest-static] list-with-trader {index}/{len(targets['traders'])} done: "
            f"{trader_name} ({time.monotonic() - item_started_at:.2f}s)"
        )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": {
                **files,
                "all": f"{PUBLIC_BASE_PATH}/v3/all.json",
                "feed": f"{PUBLIC_BASE_PATH}/v3/feed.json",
                "completion_graph": f"{PUBLIC_BASE_PATH}/v3/completion-graph.json",
            },
            "counts": {
                "details": len(files["details"]),
                "list_with_trader": len(files["list_with_trader"]),
            },
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated quest static JSON: "
        f"details={len(files['details'])}, "
        f"list_with_trader={len(files['list_with_trader'])}, "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_quest_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 22, tz="Asia/Seoul"),
    schedule="15 5 * * *",
    tags=["quest", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_quest_static_json_task = PythonOperator(
        task_id="generate_quest_static_json",
        python_callable=generate_quest_static_json,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

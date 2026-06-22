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
PUBLIC_BASE_PATH = "/static/story"
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
    print("[story-static] fetch targets from database")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                select id
                from story
                order by sort_order, title_en, id;
                """
            )
            stories = [row[0] for row in cursor.fetchall()]

    print(f"[story-static] targets fetched: stories={len(stories)}")
    return {"stories": stories}


def generate_story_static_json(postgres_conn_id):
    started_at = time.monotonic()
    targets = _fetch_targets(postgres_conn_id)
    root = OUTPUT_DIR / "static" / "story" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()
    files = {"details": []}

    print(f"[story-static] output root: {root}")

    print("[story-static] roadmap: start")
    item_started_at = time.monotonic()
    roadmap_payload = _fetch_json("/story/v3/roadmap")
    _write_json_atomic(root / "roadmap.json", roadmap_payload)
    print(
        "[story-static] roadmap: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    for index, story_id in enumerate(targets["stories"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[story-static] details {index}/{len(targets['stories'])}: "
            f"{story_id}"
        )
        payload = _fetch_json(f"/story/v3/detail/{quote(story_id, safe='')}")
        filename = f"{_safe_filename(story_id)}.json"
        _write_json_atomic(root / "details" / filename, payload)
        files["details"].append(
            {
                "id": story_id,
                "path": f"{PUBLIC_BASE_PATH}/v3/details/{filename}",
            }
        )
        print(
            f"[story-static] details {index}/{len(targets['stories'])} done: "
            f"{story_id} ({time.monotonic() - item_started_at:.2f}s)"
        )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": {
                **files,
                "roadmap": f"{PUBLIC_BASE_PATH}/v3/roadmap.json",
            },
            "counts": {"details": len(files["details"])},
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated story static JSON: "
        f"details={len(files['details'])}, "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_story_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 22, tz="Asia/Seoul"),
    schedule="45 5 * * *",
    tags=["story", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_story_static_json_task = PythonOperator(
        task_id="generate_story_static_json",
        python_callable=generate_story_static_json,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

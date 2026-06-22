import json
import os
import time
from pathlib import Path

import pendulum
import requests
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

API_BASE_URL = "https://back.eftlibrary.com/api"
OUTPUT_DIR = Path("/opt/airflow/next-public")
PUBLIC_BASE_PATH = "/static/news"
REQUEST_TIMEOUT = 60


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


def generate_news_static_json():
    started_at = time.monotonic()
    root = OUTPUT_DIR / "static" / "news" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()

    print(f"[news-static] output root: {root}")

    print("[news-static] wipe: start")
    item_started_at = time.monotonic()
    wipe_payload = _fetch_json("/news/v3/wipe")
    _write_json_atomic(root / "wipe.json", wipe_payload)
    print(
        "[news-static] wipe: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": {
                "wipe": f"{PUBLIC_BASE_PATH}/v3/wipe.json",
            },
            "counts": {"files": 1},
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated news static JSON: "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_news_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 22, tz="Asia/Seoul"),
    schedule="35 6 * * *",
    tags=["news", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_news_static_json_task = PythonOperator(
        task_id="generate_news_static_json",
        python_callable=generate_news_static_json,
    )

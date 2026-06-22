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
PUBLIC_BASE_PATH = "/static/map"
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
    print("[map-static] fetch targets from database")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                select normalized_name
                from maps
                where is_use is true
                  and normalized_name is not null
                order by sort_order, name_en, normalized_name;
                """
            )
            maps = [row[0] for row in cursor.fetchall()]

    print(f"[map-static] targets fetched: maps={len(maps)}")
    return {"maps": maps}


def generate_map_static_json(postgres_conn_id):
    started_at = time.monotonic()
    targets = _fetch_targets(postgres_conn_id)
    root = OUTPUT_DIR / "static" / "map" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()
    files = {"details": []}

    print(f"[map-static] output root: {root}")

    for index, normalized_name in enumerate(targets["maps"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[map-static] details {index}/{len(targets['maps'])}: "
            f"{normalized_name}"
        )
        payload = _fetch_json(f"/map/v3/detail/{quote(normalized_name, safe='')}")
        filename = f"{_safe_filename(normalized_name)}.json"
        _write_json_atomic(root / "details" / filename, payload)
        files["details"].append(
            {
                "id": normalized_name,
                "path": f"{PUBLIC_BASE_PATH}/v3/details/{filename}",
            }
        )
        print(
            f"[map-static] details {index}/{len(targets['maps'])} done: "
            f"{normalized_name} ({time.monotonic() - item_started_at:.2f}s)"
        )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": files,
            "counts": {"details": len(files["details"])},
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated map static JSON: "
        f"details={len(files['details'])}, "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_map_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 22, tz="Asia/Seoul"),
    schedule="30 5 * * *",
    tags=["map", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_map_static_json_task = PythonOperator(
        task_id="generate_map_static_json",
        python_callable=generate_map_static_json,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

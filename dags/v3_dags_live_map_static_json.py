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
PUBLIC_BASE_PATH = "/static/live-map"
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


def _write_bytes_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")

    with open(tmp_path, "wb") as f:
        f.write(content)

    os.replace(tmp_path, path)


def _download_file(url, path):
    print(f"[live-map-static] download asset: {url} -> {path}")
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    _write_bytes_atomic(path, response.content)


def _localize_map_floor_images(payload, normalized_name, root):
    floors = ((payload.get("data") or {}).get("floors")) or []
    for floor in floors:
        image_url = floor.get("image")
        if not image_url or not image_url.startswith(("http://", "https://")):
            continue

        floor_no = floor.get("floor_no")
        floor_id = floor.get("id")
        filename_parts = [
            _safe_filename(normalized_name),
            _safe_filename(floor_no if floor_no is not None else floor_id),
        ]
        filename = "-".join(filename_parts) + ".svg"
        asset_path = root / "assets" / "maps" / filename

        _download_file(image_url, asset_path)
        floor["image"] = f"{PUBLIC_BASE_PATH}/v3/assets/maps/{filename}"


def _fetch_targets(postgres_conn_id):
    print("[live-map-static] fetch targets from database")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                select m.normalized_name
                from maps m
                         join live_map_floors lmf on lmf.map_id = m.id
                where m.normalized_name is not null
                group by m.id, m.normalized_name, m.sort_order, m.name_en
                order by m.sort_order, m.name_en, m.normalized_name;
                """
            )
            maps = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                select q.normalized_name
                from quests q
                where q.normalized_name is not null
                  and exists (
                      select 1
                      from live_map_points lmp
                      where lmp.quest_id = q.id
                  )
                order by q.sort_order, q.name_en, q.normalized_name;
                """
            )
            quests = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                select s.id
                from story s
                where exists (
                          select 1
                          from live_map_story_points lmsp
                          where lmsp.story_id = s.id
                      )
                   or exists (
                          select 1
                          from live_map_story_requirement_points lmsrp
                          where lmsrp.story_id = s.id
                      )
                order by s.sort_order, s.title_en, s.id;
                """
            )
            stories = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                select e.id
                from live_map_events e
                where e.is_active is true
                  and exists (
                      select 1
                      from live_map_event_points lmep
                      where lmep.event_id = e.id
                  )
                order by e.sort_order, e.title_en, e.id;
                """
            )
            events = [row[0] for row in cursor.fetchall()]

    targets = {
        "maps": maps,
        "quests": quests,
        "stories": stories,
        "events": events,
    }
    print(
        "[live-map-static] targets fetched: "
        f"maps={len(maps)}, quests={len(quests)}, "
        f"stories={len(stories)}, events={len(events)}"
    )
    return targets


def generate_live_map_static_json(postgres_conn_id):
    started_at = time.monotonic()
    targets = _fetch_targets(postgres_conn_id)
    root = OUTPUT_DIR / "static" / "live-map" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()
    files = {
        "maps": [],
        "quests": [],
        "stories": [],
        "events": [],
    }

    print(f"[live-map-static] output root: {root}")

    for index, normalized_name in enumerate(targets["maps"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[live-map-static] maps {index}/{len(targets['maps'])}: "
            f"{normalized_name}"
        )
        payload = _fetch_json(f"/live-map/v3/detail/{quote(normalized_name, safe='')}")
        _localize_map_floor_images(payload, normalized_name, root)
        filename = f"{_safe_filename(normalized_name)}.json"
        target_path = root / "maps" / filename
        _write_json_atomic(target_path, payload)
        files["maps"].append(
            {
                "id": normalized_name,
                "path": f"{PUBLIC_BASE_PATH}/v3/maps/{filename}",
            }
        )
        print(
            f"[live-map-static] maps {index}/{len(targets['maps'])} done: "
            f"{normalized_name} ({time.monotonic() - item_started_at:.2f}s)"
        )

    for index, normalized_name in enumerate(targets["quests"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[live-map-static] quests {index}/{len(targets['quests'])}: "
            f"{normalized_name}"
        )
        payload = _fetch_json(f"/live-map/v3/quest/{quote(normalized_name, safe='')}")
        filename = f"{_safe_filename(normalized_name)}.json"
        target_path = root / "quests" / filename
        _write_json_atomic(target_path, payload)
        files["quests"].append(
            {
                "id": normalized_name,
                "path": f"{PUBLIC_BASE_PATH}/v3/quests/{filename}",
            }
        )
        print(
            f"[live-map-static] quests {index}/{len(targets['quests'])} done: "
            f"{normalized_name} ({time.monotonic() - item_started_at:.2f}s)"
        )

    for index, story_id in enumerate(targets["stories"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[live-map-static] stories {index}/{len(targets['stories'])}: "
            f"{story_id}"
        )
        payload = _fetch_json(f"/live-map/v3/story/{quote(story_id, safe='')}")
        filename = f"{_safe_filename(story_id)}.json"
        target_path = root / "stories" / filename
        _write_json_atomic(target_path, payload)
        files["stories"].append(
            {
                "id": story_id,
                "path": f"{PUBLIC_BASE_PATH}/v3/stories/{filename}",
            }
        )
        print(
            f"[live-map-static] stories {index}/{len(targets['stories'])} done: "
            f"{story_id} ({time.monotonic() - item_started_at:.2f}s)"
        )

    for index, event_id in enumerate(targets["events"], start=1):
        item_started_at = time.monotonic()
        print(
            f"[live-map-static] events {index}/{len(targets['events'])}: "
            f"{event_id}"
        )
        payload = _fetch_json(f"/live-map/v3/event/{quote(event_id, safe='')}")
        filename = f"{_safe_filename(event_id)}.json"
        target_path = root / "events" / filename
        _write_json_atomic(target_path, payload)
        files["events"].append(
            {
                "id": event_id,
                "path": f"{PUBLIC_BASE_PATH}/v3/events/{filename}",
            }
        )
        print(
            f"[live-map-static] events {index}/{len(targets['events'])} done: "
            f"{event_id} ({time.monotonic() - item_started_at:.2f}s)"
        )

    print("[live-map-static] completion graph: start")
    item_started_at = time.monotonic()
    completion_graph = _fetch_json("/quest/v3/completion-graph")
    _write_json_atomic(root / "completion-graph.json", completion_graph)
    print(
        "[live-map-static] completion graph: done "
        f"({time.monotonic() - item_started_at:.2f}s)"
    )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": {
                **files,
                "completion_graph": f"{PUBLIC_BASE_PATH}/v3/completion-graph.json",
            },
            "counts": {
                "maps": len(files["maps"]),
                "quests": len(files["quests"]),
                "stories": len(files["stories"]),
                "events": len(files["events"]),
            },
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated live-map static JSON: "
        f"maps={len(files['maps'])}, "
        f"quests={len(files['quests'])}, "
        f"stories={len(files['stories'])}, "
        f"events={len(files['events'])}, "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_live_map_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 18, tz="Asia/Seoul"),
    schedule="0 5 * * *",
    tags=["live-map", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_live_map_static_json_task = PythonOperator(
        task_id="generate_live_map_static_json",
        python_callable=generate_live_map_static_json,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

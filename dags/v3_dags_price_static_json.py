import json
import os
import time
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote

import pendulum
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
PUBLIC_BASE_PATH = "/static/price"


def _safe_filename(value):
    return quote(str(value), safe="-_.")


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _write_json_atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            separators=(",", ":"),
            default=_json_default,
        )
        f.write("\n")

    with open(tmp_path, "r", encoding="utf-8") as f:
        json.load(f)

    os.replace(tmp_path, path)


def _dict_rows(cursor):
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _to_float(value):
    return float(value) if value is not None else None


def _serialize_price(row):
    return {
        "game_mode": row["game_mode"],
        "highest_trader_price": _to_float(row["highest_trader_price"]),
        "highest_trader_id": row["highest_trader_id"],
        "flea_market_price": _to_float(row["flea_market_price"]),
        "trader_count": row["trader_count"],
        "has_flea": row["has_flea"],
        "update_time": row["update_time"],
    }


def _serialize_history(row):
    return {
        "game_mode": row["game_mode"],
        "price": row["price"],
        "price_time": row["price_time"],
    }


def _serialize_trader_price(row):
    return {
        "id": row["id"],
        "game_mode": row["game_mode"],
        "trader_id": row["trader_id"],
        "price": _to_float(row["price"]),
        "trader": (
            {
                "id": row["trader_id"],
                "normalized_name": row["trader_normalized_name"],
                "name_en": row["trader_name_en"],
                "name_ko": row["trader_name_ko"],
                "name_ja": row["trader_name_ja"],
                "image": row["trader_image"],
            }
            if row["trader_normalized_name"] is not None
            else None
        ),
    }


def _build_price_tiers(rows):
    tiers = ["S", "A", "B", "C", "D", "E", "F"]
    tier_size = 100
    tier_dict = {
        tier: {"min": float("inf"), "max": 0, "list": []} for tier in tiers
    }

    for index, row in enumerate(rows[:700]):
        tier_name = tiers[index // tier_size]
        per_slot = row["per_slot"]
        tier_dict[tier_name]["min"] = min(tier_dict[tier_name]["min"], per_slot)
        tier_dict[tier_name]["max"] = max(tier_dict[tier_name]["max"], per_slot)
        tier_dict[tier_name]["list"].append(row)

    return [
        {
            "tier": tier,
            "min": 0 if not tier_dict[tier]["list"] else tier_dict[tier]["min"],
            "max": 0 if not tier_dict[tier]["list"] else tier_dict[tier]["max"],
            "list": tier_dict[tier]["list"],
        }
        for tier in tiers
    ]


def _rank_payload(rank_rows, categories=None):
    filtered = [
        row
        for row in rank_rows
        if categories is None or row["category"] in categories
    ]
    result = {}
    for game_mode in ("pvp", "pve"):
        mode_rows = [
            row for row in filtered if row["game_mode"] == game_mode
        ]
        result[f"{game_mode}_top_list"] = _build_price_tiers(mode_rows)
    return result


def _load_price_data(postgres_conn_id):
    print("[price-static] load price data from database")
    postgres_hook = PostgresHook(postgres_conn_id)

    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                """
                select i.id,
                       i.normalized_name,
                       i.name_en,
                       i.name_ko,
                       i.name_ja,
                       i.image,
                       i.category,
                       i.parent_category,
                       i.width,
                       i.height
                from items i
                where i.normalized_name is not null
                  and exists (
                      select 1
                      from item_prices ip
                      where ip.item_id = i.id
                  )
                order by i.name_en, i.normalized_name;
                """
            )
            items = _dict_rows(cursor)

            cursor.execute(
                """
                select item_id,
                       game_mode,
                       highest_trader_price,
                       highest_trader_id,
                       flea_market_price,
                       trader_count,
                       has_flea,
                       update_time
                from item_prices
                order by item_id, game_mode;
                """
            )
            prices = _dict_rows(cursor)

            cursor.execute(
                """
                select iph.item_id,
                       iph.game_mode,
                       iph.price,
                       iph.price_time
                from item_price_history iph
                join item_prices ip
                  on ip.item_id = iph.item_id
                 and ip.game_mode = iph.game_mode
                order by iph.item_id, iph.game_mode, iph.price_time;
                """
            )
            histories = _dict_rows(cursor)

            cursor.execute(
                """
                select itp.id,
                       itp.item_id,
                       itp.game_mode,
                       itp.trader_id,
                       itp.price,
                       t.normalized_name as trader_normalized_name,
                       t.name_en as trader_name_en,
                       t.name_ko as trader_name_ko,
                       t.name_ja as trader_name_ja,
                       t.image as trader_image
                from item_trader_prices itp
                         left join traders t on itp.trader_id = t.id
                order by itp.item_id, itp.game_mode, itp.price desc;
                """
            )
            trader_prices = _dict_rows(cursor)

    print(
        "[price-static] loaded: "
        f"items={len(items)}, prices={len(prices)}, "
        f"histories={len(histories)}, trader_prices={len(trader_prices)}"
    )
    return items, prices, histories, trader_prices


def generate_price_static_json(postgres_conn_id):
    started_at = time.monotonic()
    root = OUTPUT_DIR / "static" / "price" / "v3"
    generated_at = pendulum.now("UTC").to_iso8601_string()
    items, prices, histories, trader_prices = _load_price_data(postgres_conn_id)

    prices_by_item = defaultdict(dict)
    histories_by_item = defaultdict(lambda: {"pvp": [], "pve": []})
    trader_prices_by_item = defaultdict(lambda: {"pvp": [], "pve": []})

    for price in prices:
        prices_by_item[price["item_id"]][price["game_mode"]] = _serialize_price(price)

    for history in histories:
        histories_by_item[history["item_id"]].setdefault(
            history["game_mode"], []
        ).append(_serialize_history(history))

    for trader_price in trader_prices:
        trader_prices_by_item[trader_price["item_id"]].setdefault(
            trader_price["game_mode"], []
        ).append(_serialize_trader_price(trader_price))

    files = {"details": [], "rank_categories": []}
    search_index = []
    rank_rows = []

    print(f"[price-static] output root: {root}")

    for index, item in enumerate(items, start=1):
        detail = {
            "id": item["id"],
            "normalized_name": item["normalized_name"],
            "name_en": item["name_en"],
            "name_ko": item["name_ko"],
            "name_ja": item["name_ja"],
            "image": item["image"],
            "category": item["category"],
            "parent_category": item["parent_category"],
            "width": item["width"],
            "height": item["height"],
            "prices": {
                "pvp": prices_by_item[item["id"]].get("pvp"),
                "pve": prices_by_item[item["id"]].get("pve"),
            },
            "history_by_type": histories_by_item[item["id"]],
            "trader_prices": trader_prices_by_item[item["id"]],
        }

        search_index.append(
            {
                "id": item["id"],
                "normalized_name": item["normalized_name"],
                "name_en": item["name_en"],
                "name_ko": item["name_ko"],
                "name_ja": item["name_ja"],
                "image": item["image"],
                "category": item["category"],
                "parent_category": item["parent_category"],
                "width": item["width"],
                "height": item["height"],
                "prices": detail["prices"],
            }
        )

        for game_mode, price in detail["prices"].items():
            if (
                price is None
                or price["flea_market_price"] is None
                or item["width"] is None
                or item["height"] is None
                or item["width"] <= 0
                or item["height"] <= 0
            ):
                continue
            per_slot = price["flea_market_price"] / (item["width"] * item["height"])
            rank_rows.append(
                {
                    "id": item["id"],
                    "normalized_name": item["normalized_name"],
                    "name_en": item["name_en"],
                    "name_ko": item["name_ko"],
                    "name_ja": item["name_ja"],
                    "image": item["image"],
                    "width": item["width"],
                    "height": item["height"],
                    "category": item["category"],
                    "game_mode": game_mode,
                    "flea_market_price": price["flea_market_price"],
                    "highest_trader_price": price["highest_trader_price"],
                    "highest_trader_id": price["highest_trader_id"],
                    "per_slot": per_slot,
                }
            )

        filename = f"{_safe_filename(item['normalized_name'])}.json"
        _write_json_atomic(
            root / "details" / filename,
            {"status": 200, "msg": "OK", "data": detail},
        )
        files["details"].append(
            {
                "id": item["normalized_name"],
                "path": f"{PUBLIC_BASE_PATH}/v3/details/{filename}",
            }
        )

        if index % 500 == 0:
            print(f"[price-static] details written: {index}/{len(items)}")

    rank_rows.sort(key=lambda row: row["per_slot"], reverse=True)
    categories = sorted({row["category"] for row in rank_rows if row["category"]})

    _write_json_atomic(
        root / "search-index.json",
        {"status": 200, "msg": "OK", "data": search_index},
    )
    _write_json_atomic(
        root / "rank" / "all.json",
        {"status": 200, "msg": "OK", "data": _rank_payload(rank_rows)},
    )

    for category in categories:
        filename = f"{_safe_filename(category)}.json"
        _write_json_atomic(
            root / "rank" / "categories" / filename,
            {
                "status": 200,
                "msg": "OK",
                "data": _rank_payload(rank_rows, {category}),
            },
        )
        files["rank_categories"].append(
            {
                "id": category,
                "path": f"{PUBLIC_BASE_PATH}/v3/rank/categories/{filename}",
            }
        )

    index_payload = {
        "status": 200,
        "msg": "OK",
        "generated_at": generated_at,
        "api_base_url": API_BASE_URL,
        "data": {
            "files": {
                **files,
                "search_index": f"{PUBLIC_BASE_PATH}/v3/search-index.json",
                "rank_all": f"{PUBLIC_BASE_PATH}/v3/rank/all.json",
            },
            "counts": {
                "details": len(files["details"]),
                "rank_categories": len(files["rank_categories"]),
            },
        },
    }
    _write_json_atomic(root / "index.json", index_payload)

    print(
        "Generated price static JSON: "
        f"details={len(files['details'])}, "
        f"rank_categories={len(files['rank_categories'])}, "
        f"output={root}, "
        f"elapsed={time.monotonic() - started_at:.2f}s"
    )


with DAG(
    dag_id="v3_dags_price_static_json",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 6, 22, tz="Asia/Seoul"),
    schedule="35 * * * *",
    tags=["price", "static-json", "next-public"],
    catchup=False,
) as dag:
    generate_price_static_json_task = PythonOperator(
        task_id="generate_price_static_json",
        python_callable=generate_price_static_json,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

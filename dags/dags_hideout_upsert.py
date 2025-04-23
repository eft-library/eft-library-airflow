import json
import os

from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_function import read_sql
from custom_module.graphql_function import get_graphql
from custom_module.hideout_func import (
    generate_hideout_stations_graphql,
    v2_hideout_master_process,
    v2_hideout_level_process,
    v2_hideout_item_require_process,
    v2_hideout_trader_process,
    v2_hideout_station_require_process,
    v2_hideout_skill_require_process,
    v2_hideout_bonus_process,
    v2_hideout_crafts_process,
)


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/hideout_en_list.json"
ko_path = "/opt/airflow/tmp/hideout_ko_list.json"
ja_path = "/opt/airflow/tmp/hideout_ja_list.json"

with DAG(
    dag_id="dags_hideout_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="10 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_hideout_list(**kwargs):
        item_list_en = get_graphql(generate_hideout_stations_graphql("en"))
        item_list_ko = get_graphql(generate_hideout_stations_graphql("ko"))
        item_list_ja = get_graphql(generate_hideout_stations_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["hideoutStations"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["hideoutStations"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["hideoutStations"], f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }

    def upsert_hideout_master(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_master.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql, v2_hideout_master_process(item_en, item_ko, item_ja)
                    )
            conn.commit()

    def upsert_hideout_level(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict.keys())

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_level.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    for level in item_en["levels"]:
                        cursor.execute(sql, v2_hideout_level_process(level))
            conn.commit()

    def upsert_hideout_item_require(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_item_require.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["levels"], item_ko["levels"], item_ja["levels"]
                    ):
                        for require_en, require_ko, require_ja in zip(
                            level_en["itemRequirements"],
                            level_ko["itemRequirements"],
                            level_ja["itemRequirements"],
                        ):
                            cursor.execute(
                                sql,
                                v2_hideout_item_require_process(
                                    level_en.get("id"),
                                    require_en,
                                    require_ko,
                                    require_ja,
                                ),
                            )

            conn.commit()

    def upsert_hideout_trader_require(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_trader_require.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["levels"], item_ko["levels"], item_ja["levels"]
                    ):
                        for trader_en, trader_ko, trader_ja in zip(
                            level_en["traderRequirements"],
                            level_ko["traderRequirements"],
                            level_ja["traderRequirements"],
                        ):
                            cursor.execute(
                                sql,
                                v2_hideout_trader_process(
                                    level_en.get("id"), trader_en, trader_ko, trader_ja
                                ),
                            )

            conn.commit()

    def upsert_hideout_station_require(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_station_require.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["levels"], item_ko["levels"], item_ja["levels"]
                    ):
                        for trader_en, trader_ko, trader_ja in zip(
                            level_en["stationLevelRequirements"],
                            level_ko["stationLevelRequirements"],
                            level_ja["stationLevelRequirements"],
                        ):
                            cursor.execute(
                                sql,
                                v2_hideout_station_require_process(
                                    level_en.get("id"), trader_en, trader_ko, trader_ja
                                ),
                            )

            conn.commit()

    def upsert_hideout_skill_require(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_skill_require.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["levels"], item_ko["levels"], item_ja["levels"]
                    ):
                        for trader_en, trader_ko, trader_ja in zip(
                            level_en["skillRequirements"],
                            level_ko["skillRequirements"],
                            level_ja["skillRequirements"],
                        ):
                            cursor.execute(
                                sql,
                                v2_hideout_skill_require_process(
                                    level_en.get("id"), trader_en, trader_ko, trader_ja
                                ),
                            )

            conn.commit()

    def upsert_hideout_bonus(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_bonus.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["levels"], item_ko["levels"], item_ja["levels"]
                    ):
                        for trader_en, trader_ko, trader_ja in zip(
                            level_en["bonuses"],
                            level_ko["bonuses"],
                            level_ja["bonuses"],
                        ):
                            cursor.execute(
                                sql,
                                v2_hideout_bonus_process(
                                    level_en.get("id"), trader_en, trader_ko, trader_ja
                                ),
                            )

            conn.commit()

    def upsert_hideout_crafts(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_hideout_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = (
            set(item_en_dict.keys())
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_hideout_crafts.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    for level_en, level_ko, level_ja in zip(
                        item_en["crafts"], item_ko["crafts"], item_ja["crafts"]
                    ):
                        cursor.execute(
                            sql,
                            v2_hideout_crafts_process(level_en, level_ko, level_ja),
                        )

            conn.commit()

    def remove_json_files(**kwargs):
        files = [
            en_path,
            ko_path,
            ja_path,
        ]

        for path in files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"Deleted: {path}")
                else:
                    print(f"File not found: {path}")
            except Exception as e:
                print(f"Error deleting {path}: {e}")

    fetch_data = PythonOperator(
        task_id="fetch_hideout_list", python_callable=fetch_hideout_list
    )

    upsert_hideout_master_task = PythonOperator(
        task_id="upsert_hideout_master",
        python_callable=upsert_hideout_master,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_level_task = PythonOperator(
        task_id="upsert_hideout_level",
        python_callable=upsert_hideout_level,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_item_require_task = PythonOperator(
        task_id="upsert_hideout_item_require",
        python_callable=upsert_hideout_item_require,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_trader_require_task = PythonOperator(
        task_id="upsert_hideout_trader_require",
        python_callable=upsert_hideout_trader_require,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_station_require_task = PythonOperator(
        task_id="upsert_hideout_station_require",
        python_callable=upsert_hideout_station_require,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_skill_require_task = PythonOperator(
        task_id="upsert_hideout_skill_require",
        python_callable=upsert_hideout_skill_require,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_bonus_task = PythonOperator(
        task_id="upsert_hideout_bonus",
        python_callable=upsert_hideout_bonus,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    upsert_hideout_crafts_task = PythonOperator(
        task_id="upsert_hideout_crafts",
        python_callable=upsert_hideout_crafts,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        provide_context=True,
    )

    (
        fetch_data
        >> [
            upsert_hideout_master_task,
            upsert_hideout_level_task,
            upsert_hideout_item_require_task,
            upsert_hideout_trader_require_task,
            upsert_hideout_station_require_task,
            upsert_hideout_skill_require_task,
            upsert_hideout_bonus_task,
            upsert_hideout_crafts_task,
        ]
        >> remove_json_files_task
    )

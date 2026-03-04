import json
import os

from airflow import DAG
import pendulum
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from custom_module.graphql_func import get_graphql
from custom_module.item_func import check_category, generate_item_graphql
from custom_module.item.weapon_func import (
    v2_gun_process,
    v2_knife_process,
    v2_throwable_process,
)
from custom_module.item.general_func import (
    v2_rig_process,
    v2_armor_vest_process,
    v2_headset_process,
    v2_backpack_process,
    v2_container_process,
    v2_loot_process,
    v2_arm_band_process,
    v2_glasses_process,
    v2_other_process,
)
from custom_module.item.ricochet_item_func import (
    v2_headwear_process,
    v2_face_cover_process,
)
from custom_module.item.ammo_func import v2_ammo_process
from custom_module.item.key_func import v2_key_process, process_key_map
from custom_module.item.provisions_func import v2_provisions_process
from custom_module.item.medical_func import v2_medical_process

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/item_en_list.json"
ko_path = "/opt/airflow/tmp/item_ko_list.json"
ja_path = "/opt/airflow/tmp/item_ja_list.json"

with DAG(
    dag_id="dags_item_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule="30 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_item_list():
        item_list_en = get_graphql(generate_item_graphql("en"))
        item_list_ko = get_graphql(generate_item_graphql("ko"))
        item_list_ja = get_graphql(generate_item_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"], f)

        return {
            "en": en_path,
            "ko": ko_path,
            "ja": ja_path,
        }


    def upsert_gun(postgres_conn_id):
        # 최신 문법: 컨텍스트는 함수 내부에서 가져온다
        context = get_current_context()
        ti = context["ti"]

        # XCom에서 파일 경로 가져오기
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        # JSON 로딩
        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        # dict 변환
        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}

        # 카테고리 필터
        filtered_items = check_category(item_en_list["items"], "Gun")

        # id 교집합 필터링
        item_ids = (
                set(item["id"] for item in filtered_items)
                & set(item_ko_dict.keys())
                & set(item_ja_dict.keys())
        )

        # DB 연결
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        # UPSERT
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql,
                        v2_gun_process(item_en, item_ko, item_ja),
                    )
            conn.commit()

    def upsert_knife(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Knife")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_knife_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_throwable(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Throwable weapon")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_throwable_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_rig(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Chest rig")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_rig_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_armor_vest(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Armor")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql, v2_armor_vest_process(item_en, item_ko, item_ja)
                    )
            conn.commit()

    def upsert_headwear(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Headwear")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_headwear_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_headset(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Headphones")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_headset_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_backpack(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Backpack")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_backpack_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_container(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Common container")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_container_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_loot(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Loot")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_loot_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_arm_band(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Arm Band")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_arm_band_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_glasses(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Vis. observ. device")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_glasses_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_face_cover(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Face Cover")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql, v2_face_cover_process(item_en, item_ko, item_ja)
                    )
            conn.commit()

    def upsert_ammo(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Ammo")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_ammo_process(item_en, item_ko, item_ja))
            conn.commit()

    def upsert_key(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Key")

        en_key_map = process_key_map(item_en_list["maps"])
        ko_key_map = process_key_map(item_ko_list["maps"])
        ja_key_map = process_key_map(item_ja_list["maps"])

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql,
                        v2_key_process(
                            item_en,
                            item_ko,
                            item_ja,
                            en_key_map,
                            ko_key_map,
                            ja_key_map,
                        ),
                    )
            conn.commit()

    def upsert_provisions(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Provisions")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(
                        sql, v2_provisions_process(item_en, item_ko, item_ja)
                    )
            conn.commit()

    def upsert_medical(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Meds")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_medical_process(item_en, item_ko, item_ja))
            conn.commit()

    def other_category_item(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_item_list")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list["items"]}
        item_ko_dict = {item["id"]: item for item in item_ko_list["items"]}
        item_ja_dict = {item["id"]: item for item in item_ja_list["items"]}
        filtered_items = check_category(item_en_list["items"], "Other")

        item_ids = (
            set(item["id"] for item in filtered_items)
            & set(item_ko_dict.keys())
            & set(item_ja_dict.keys())
        )

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("upsert_item.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for item_id in item_ids:
                    item_en = item_en_dict[item_id]
                    item_ko = item_ko_dict[item_id]
                    item_ja = item_ja_dict[item_id]

                    cursor.execute(sql, v2_other_process(item_en, item_ko, item_ja))
            conn.commit()

    def remove_json_files():
        files = [en_path, ko_path, ja_path]

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
        task_id="fetch_item_list", python_callable=fetch_item_list
    )

    upsert_gun_task = PythonOperator(
        task_id="upsert_gun",
        python_callable=upsert_gun,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_knife_task = PythonOperator(
        task_id="upsert_knife",
        python_callable=upsert_knife,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_throwable_task = PythonOperator(
        task_id="upsert_throwable",
        python_callable=upsert_throwable,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_rig_task = PythonOperator(
        task_id="upsert_rig",
        python_callable=upsert_rig,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_armor_vest_task = PythonOperator(
        task_id="upsert_armor_vest",
        python_callable=upsert_armor_vest,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_headwear_task = PythonOperator(
        task_id="upsert_headwear",
        python_callable=upsert_headwear,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_headset_task = PythonOperator(
        task_id="upsert_headset",
        python_callable=upsert_headset,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_backpack_task = PythonOperator(
        task_id="upsert_backpack",
        python_callable=upsert_backpack,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_container_task = PythonOperator(
        task_id="upsert_container",
        python_callable=upsert_container,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_loot_task = PythonOperator(
        task_id="upsert_loot",
        python_callable=upsert_loot,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_arm_band_task = PythonOperator(
        task_id="upsert_arm_band",
        python_callable=upsert_arm_band,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_glasses_task = PythonOperator(
        task_id="upsert_glasses",
        python_callable=upsert_glasses,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_face_cover_task = PythonOperator(
        task_id="upsert_face_cover",
        python_callable=upsert_face_cover,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_ammo_task = PythonOperator(
        task_id="upsert_ammo",
        python_callable=upsert_ammo,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_key_task = PythonOperator(
        task_id="upsert_key",
        python_callable=upsert_key,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_provisions_task = PythonOperator(
        task_id="upsert_provisions",
        python_callable=upsert_provisions,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_medical_task = PythonOperator(
        task_id="upsert_medical",
        python_callable=upsert_medical,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_other_task = PythonOperator(
        task_id="upsert_other",
        python_callable=other_category_item,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    upsert_tasks = [
        upsert_gun_task,
        upsert_knife_task,
        upsert_throwable_task,
        upsert_rig_task,
        upsert_armor_vest_task,
        upsert_headwear_task,
        upsert_headset_task,
        upsert_backpack_task,
        upsert_container_task,
        upsert_loot_task,
        upsert_arm_band_task,
        upsert_glasses_task,
        upsert_face_cover_task,
        upsert_ammo_task,
        upsert_key_task,
        upsert_provisions_task,
        upsert_medical_task,
        upsert_other_task,
    ]

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
    )

    fetch_data >> upsert_tasks >> remove_json_files_task

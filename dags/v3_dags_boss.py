import json
import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values

from custom_module.graphql_func import get_graphql
from custom_module.v3.boss_task_func import (
    generate_boss_graphql,
    v3_boss_process,
    v3_boss_item_process,
)

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_boss_en_list.json"
ko_path = "/opt/airflow/tmp/v3_boss_ko_list.json"
ja_path = "/opt/airflow/tmp/v3_boss_ja_list.json"

with DAG(
    dag_id="v3_dags_boss",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="10 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_boss():
        item_list_en = get_graphql(generate_boss_graphql("en"))
        item_list_ko = get_graphql(generate_boss_graphql("ko"))
        item_list_ja = get_graphql(generate_boss_graphql("ja"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["bosses"], f)
        with open(ko_path, "w") as f:
            json.dump(item_list_ko["data"]["bosses"], f)
        with open(ja_path, "w") as f:
            json.dump(item_list_ja["data"]["bosses"], f)

        return {"en": en_path, "ko": ko_path, "ja": ja_path}

    def upsert_boss(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_boss")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)
        with open(item_paths["ko"], "r") as f:
            item_ko_list = json.load(f)
        with open(item_paths["ja"], "r") as f:
            item_ja_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}
        item_ko_dict = {item["id"]: item for item in item_ko_list}
        item_ja_dict = {item["id"]: item for item in item_ja_list}

        item_ids = sorted(set(item_en_dict) & set(item_ko_dict) & set(item_ja_dict))

        boss_rows = []
        boss_item_rows = []

        for item_id in item_ids:
            item_en = item_en_dict[item_id]
            item_ko = item_ko_dict[item_id]
            item_ja = item_ja_dict[item_id]

            boss_rows.append(v3_boss_process(item_en, item_ko, item_ja))

            boss_item_rows.extend(v3_boss_item_process(item_en))

        if not boss_rows:
            return

        boss_sql = """
            insert into bosses (
                id, name_en, name_ko, name_ja, image, normalized_name,
                health_total, head_hp, thorax_hp, stomach_hp,
                left_arm_hp, right_arm_hp, left_leg_hp, right_leg_hp
            )
            values %s
            ON CONFLICT (id) DO UPDATE
            SET
                name_en = EXCLUDED.name_en,
                name_ko = EXCLUDED.name_ko,
                name_ja = EXCLUDED.name_ja,
                image = EXCLUDED.image,
                normalized_name = EXCLUDED.normalized_name,
                health_total = EXCLUDED.health_total,
                head_hp = EXCLUDED.head_hp,
                thorax_hp = EXCLUDED.thorax_hp,
                stomach_hp = EXCLUDED.stomach_hp,
                left_arm_hp = EXCLUDED.left_arm_hp,
                right_arm_hp = EXCLUDED.right_arm_hp,
                left_leg_hp = EXCLUDED.left_leg_hp,
                right_leg_hp = EXCLUDED.right_leg_hp
        """

        boss_item_sql = """
            insert into boss_item (boss_id, item_id, quantity)
            values %s
            ON CONFLICT (boss_id, item_id) DO UPDATE
            SET quantity = EXCLUDED.quantity
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                execute_values(
                    cursor,
                    boss_sql,
                    boss_rows,
                    page_size=500,
                )

                if boss_item_rows:
                    execute_values(
                        cursor,
                        boss_item_sql,
                        boss_item_rows,
                        page_size=500,
                    )

            conn.commit()

    fetch_data_task = PythonOperator(
        task_id="fetch_boss",
        python_callable=fetch_boss,
    )

    upsert_boss_task = PythonOperator(
        task_id="upsert_boss",
        python_callable=upsert_boss,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    fetch_data_task >> upsert_boss_task

import json
import pendulum
import os
from html import escape

from airflow import DAG
from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.standard.operators.python import BranchPythonOperator, PythonOperator
from airflow.sdk import get_current_context
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from psycopg2.extras import execute_values
from airflow.task.trigger_rule import TriggerRule

from custom_module.graphql_func import get_graphql
from custom_module.v3.map_task_func import generate_map_graphql, v3_map_process

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

en_path = "/opt/airflow/tmp/v3_map_en_list.json"

MANUAL_MAP_IDS = {
    "CUSTOMS_GA_FIRST_FLOOR_DORMITORY",
    "CUSTOMS_GA_SECOND_FLOOR_DORMITORY",
    "CUSTOMS_GA_THIRD_FLOOR_DORMITORY",
    "CUSTOMS_INTELROOM_FIRST_FLOOR",
    "CUSTOMS_INTELROOM_SECOND_FLOOR",
    "CUSTOMS_NA_FIRST_FLOOR_DORMITORY",
    "CUSTOMS_NA_SECOND_FLOOR_DORMITORY",
    "FACTORY_SECOND_FLOOR",
    "FACTORY_THIRD_FLOOR",
    "FACTORY_UNDERGROUND",
    "GROUND_ZERO_UNDERGROUND",
    "RESERVE_UNDERGROUND",
    "SHORELINE_RESORT",
    "THE_LAB_SECOND_FLOOR",
    "THE_LAB_UNDERGROUND",
}

with DAG(
    dag_id="v3_dags_map",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="1 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def fetch_map():
        item_list_en = get_graphql(generate_map_graphql("en"))

        with open(en_path, "w") as f:
            json.dump(item_list_en["data"]["maps"], f)

        return {"en": en_path}

    def compare_map(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_map")

        with open(item_paths["en"], "r") as f:
            api_maps = json.load(f)

        api_by_id = {
            item["id"]: {
                "name_en": item.get("name"),
                "normalized_name": item.get("normalizedName"),
            }
            for item in api_maps
        }

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(
                    """
                    select id, name_en, normalized_name
                    from maps
                    """
                )
                db_by_id = {
                    str(row[0]): {
                        "name_en": row[1],
                        "normalized_name": row[2],
                    }
                    for row in cursor.fetchall()
                }

        api_ids = set(api_by_id)
        db_ids = set(db_by_id)
        added = [
            {
                "id": map_id,
                "name": api_by_id[map_id]["name_en"] or map_id,
            }
            for map_id in sorted(api_ids - db_ids)
        ]
        deleted = [
            {
                "id": map_id,
                "name": db_by_id[map_id]["name_en"] or map_id,
            }
            for map_id in sorted(db_ids - api_ids - MANUAL_MAP_IDS)
        ]

        field_labels = {
            "name_en": "영문 이름",
            "normalized_name": "정규화 이름",
        }
        changed = []
        for map_id in sorted(api_ids & db_ids):
            changed_fields = [
                field_labels[field]
                for field in field_labels
                if api_by_id[map_id][field] != db_by_id[map_id][field]
            ]
            if changed_fields:
                changed.append(
                    {
                        "id": map_id,
                        "name": api_by_id[map_id]["name_en"]
                        or db_by_id[map_id]["name_en"]
                        or map_id,
                        "fields": changed_fields,
                    }
                )

        def render_items(title, items, field_key=None):
            if not items:
                return ""

            lines = []
            for item in items:
                label = f'{escape(str(item["name"]))} ({escape(str(item["id"]))})'
                if field_key:
                    fields = ", ".join(escape(field) for field in item[field_key])
                    label = f"{label}: {fields}"
                lines.append(f"<li>{label}</li>")
            return f"<h3>{title} ({len(items)}건)</h3><ul>{''.join(lines)}</ul>"

        change_count = len(added) + len(deleted) + len(changed)
        html_content = "".join(
            [
                "<h2>Map API 데이터 변경 내역</h2>",
                render_items("추가", added),
                render_items("삭제", deleted),
                render_items("변경", changed, "fields"),
            ]
        )

        return {
            "change_count": change_count,
            "added": added,
            "deleted": deleted,
            "changed": changed,
            "html_content": html_content,
        }

    def choose_email_branch():
        context = get_current_context()
        diff = context["ti"].xcom_pull(task_ids="compare_map") or {}
        if diff.get("change_count", 0) > 0:
            return "send_change_email"
        return "no_map_changes"

    def upsert_map(postgres_conn_id):
        context = get_current_context()
        ti = context["ti"]
        item_paths = ti.xcom_pull(task_ids="fetch_map")

        with open(item_paths["en"], "r") as f:
            item_en_list = json.load(f)

        item_en_dict = {item["id"]: item for item in item_en_list}

        item_ids = set(item_en_dict)

        rows = [
            v3_map_process(
                item_en_dict[item_id],
                None,
                None,
            )
            for item_id in item_ids
        ]

        if not rows:
            return

        sql = """
            INSERT INTO maps (
                id,
                normalized_name,
                name_en,
                name_ko,
                name_ja
            )
            VALUES %s
            ON CONFLICT (id) DO UPDATE
            SET
                normalized_name = EXCLUDED.normalized_name,
                name_en = EXCLUDED.name_en
        """

        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                execute_values(
                    cursor,
                    sql,
                    rows,
                    page_size=500,
                )
            conn.commit()

    def remove_json_files():
        files = [
            en_path,
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

    fetch_map_task = PythonOperator(
        task_id="fetch_map",
        python_callable=fetch_map,
    )

    compare_map_task = PythonOperator(
        task_id="compare_map",
        python_callable=compare_map,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    upsert_map_task = PythonOperator(
        task_id="upsert_map",
        python_callable=upsert_map,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    remove_json_files_task = PythonOperator(
        task_id="remove_json_files",
        python_callable=remove_json_files,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    choose_email_branch_task = BranchPythonOperator(
        task_id="choose_email_branch",
        python_callable=choose_email_branch,
    )

    send_change_email_task = EmailOperator(
        task_id="send_change_email",
        to=["poeynus@gmail.com"],
        subject="[EFT Library] Map API 데이터 변경 감지",
        html_content="{{ ti.xcom_pull(task_ids='compare_map')['html_content'] }}",
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    no_map_changes_task = EmptyOperator(task_id="no_map_changes")

    fetch_map_task >> compare_map_task >> upsert_map_task
    upsert_map_task >> remove_json_files_task
    upsert_map_task >> choose_email_branch_task
    choose_email_branch_task >> [send_change_email_task, no_map_changes_task]

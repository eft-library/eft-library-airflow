from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from contextlib import closing
import pendulum
from custom_module.psql_func import read_sql

BATCH_SIZE = 500
MAX_BATCHES = 10  # 최대 10개 batch로 가정

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_item_detail_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="50 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def get_total_count(postgres_conn_id, **context):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_count.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
                total_count = cursor.fetchone()[0]
            conn.commit()

        context["ti"].xcom_push(key="total_count", value=total_count)

    def process_batch(postgres_conn_id, offset_count, limit, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_detail_upsert.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql, {"offset_count": offset_count, "limit": limit})
            conn.commit()
        print(f"Processed batch {offset_count} ~ {offset_count + limit}")

    task_get_total_count = PythonOperator(
        task_id="get_total_count",
        python_callable=get_total_count,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    with TaskGroup(group_id="batch_tasks") as batch_tasks:
        for i in range(MAX_BATCHES):
            offset = i * BATCH_SIZE
            task = PythonOperator(
                task_id=f"process_batch_{i}",
                python_callable=process_batch,
                op_kwargs={
                    "postgres_conn_id": "tkl_db",
                    "offset_count": offset,
                    "limit": BATCH_SIZE,
                },
            )
            task_get_total_count >> task

    task_get_total_count >> batch_tasks

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from contextlib import closing
import pendulum
from custom_module.psql_func import read_sql

BATCH_SIZE = 500

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_item_detail_upsert_parallel",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="50 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
    max_active_tasks=10,  # 병렬 작업 수 제한 가능
) as dag:

    def get_total_count(postgres_conn_id, **context):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_count.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
                total_count = cursor.fetchone()[0]
            conn.commit()
        return total_count

    def process_batch(postgres_conn_id, start: int, end: int, **kwargs):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_detail_upsert.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql, (start, end))
            conn.commit()

    get_total_count_task = PythonOperator(
        task_id="get_total_count",
        python_callable=get_total_count,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    def generate_batch_tasks(**kwargs):
        ti = kwargs["ti"]
        total_count = ti.xcom_pull(task_ids="get_total_count")

        with TaskGroup(group_id="batch_upserts") as tg:
            for start in range(0, total_count, BATCH_SIZE):
                end = start + BATCH_SIZE
                PythonOperator(
                    task_id=f"process_batch_{start}_{end}",
                    python_callable=process_batch,
                    op_kwargs={
                        "postgres_conn_id": "tkl_db",
                        "start": start,
                        "end": end,
                    },
                )
        return tg

    # TaskGroup을 동적으로 생성하는 작업
    generate_tasks = PythonOperator(
        task_id="generate_batches",
        python_callable=generate_batch_tasks,
        provide_context=True,
    )

    get_total_count_task >> generate_tasks

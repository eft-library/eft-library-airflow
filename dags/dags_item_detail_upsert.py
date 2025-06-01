from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql

BATCH_SIZE = 500

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_item_detail_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="50 0 * * *",  # 매일 00:50
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def get_batches(postgres_conn_id, **context):
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_count.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql)
                total_count = cursor.fetchone()[0]
            conn.commit()

        batches = [(start, BATCH_SIZE) for start in range(0, total_count, BATCH_SIZE)]
        context["ti"].xcom_push(key="batches", value=batches)

    def process_batch(postgres_conn_id, batch_range, **kwargs):
        offset_count, limit = batch_range
        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_detail_upsert.sql")
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(sql, {"offset_count": offset_count, "limit": limit})
            conn.commit()
        print(f"Processed batch {offset_count} ~ {offset_count + limit}")

    task_get_batches = PythonOperator(
        task_id="get_batches",
        python_callable=get_batches,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    def create_batch_tasks(**context):
        ti = context["ti"]
        batches = ti.xcom_pull(task_ids="get_batches", key="batches")
        tasks = []
        for i, batch in enumerate(batches):
            task = PythonOperator(
                task_id=f"process_batch_{i}",
                python_callable=process_batch,
                op_kwargs={
                    "postgres_conn_id": "tkl_db",
                    "batch_range": batch,
                },
            )
            tasks.append(task)
            task_get_batches >> task  # 각 배치 작업은 get_batches 이후 실행
        return tasks

    task_create_batches = PythonOperator(
        task_id="create_batch_tasks",
        python_callable=create_batch_tasks,
        provide_context=True,
    )

    task_get_batches >> task_create_batches

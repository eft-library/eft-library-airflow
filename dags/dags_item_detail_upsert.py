from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.task_group import TaskGroup
from contextlib import closing
from custom_module.psql_func import read_sql

BATCH_SIZE = 500

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}


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


def process_batch(postgres_conn_id, offset_count, limit, **kwargs):
    postgres_hook = PostgresHook(postgres_conn_id)
    sql = read_sql("item_detail_upsert.sql")
    with closing(postgres_hook.get_conn()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql, {"offset_count": offset_count, "limit": limit})
        conn.commit()
    print(f"Processed batch {offset_count} ~ {offset_count + limit}")


with DAG(
    dag_id="dags_item_detail_upsert",
    default_args=default_args,
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule_interval="50 0 * * *",  # 매일 00:50
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    task_get_batches = PythonOperator(
        task_id="get_batches",
        python_callable=get_batches,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    def generate_batch_tasks(**context):
        from airflow.operators.empty import EmptyOperator  # 종료 태스크용

        ti = context["ti"]
        batches = ti.xcom_pull(task_ids="get_batches", key="batches")

        if not batches:
            raise ValueError("No batches returned from get_batches")

        end = EmptyOperator(task_id="all_batches_done")

        with TaskGroup("batch_tasks") as batch_task_group:
            for i, (offset, limit) in enumerate(batches):
                batch_task = PythonOperator(
                    task_id=f"process_batch_{i}",
                    python_callable=process_batch,
                    op_kwargs={
                        "postgres_conn_id": "tkl_db",
                        "offset_count": offset,
                        "limit": limit,
                    },
                )
                task_get_batches >> batch_task >> end  # 의존성 연결

        return end.task_id

    task_generate_batches = PythonOperator(
        task_id="generate_batch_tasks",
        python_callable=generate_batch_tasks,
        provide_context=True,
    )

    task_get_batches >> task_generate_batches

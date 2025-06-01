from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
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

        return total_count

    def process_batch(postgres_conn_id, **kwargs):
        ti = kwargs["ti"]
        total_count = ti.xcom_pull(task_ids="get_total_count")

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_detail_upsert.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for start in range(0, total_count, BATCH_SIZE):
                    end = start + BATCH_SIZE
                    sql.format(offset_count=start, limit=end)
                    cursor.execute(sql)
            conn.commit()

    get_total_count_task = PythonOperator(
        task_id="get_total_count",
        python_callable=get_total_count,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    process_batch_task = PythonOperator(
        task_id="process_batch",
        python_callable=process_batch,
        op_kwargs={"postgres_conn_id": "tkl_db"},
        provide_context=True,
    )

    get_total_count_task >> process_batch_task

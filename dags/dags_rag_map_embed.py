from airflow import DAG
import pendulum
from airflow.providers.standard.operators.python import PythonOperator
from custom_module.rag.rag_map_func import run_map_rag_embed

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}

with DAG(
    dag_id="dags_rag_map_embed",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Seoul"),
    schedule=None,
    catchup=False,
    tags=["rag", "map"],
) as dag:

    embed_task = PythonOperator(
        task_id="embed_map_group_i18n",
        python_callable=run_map_rag_embed,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

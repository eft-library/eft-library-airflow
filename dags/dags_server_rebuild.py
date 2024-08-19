import json
import requests
from airflow import DAG
import datetime
import pendulum
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable


def trigger_server_rebuild(**kwargs):
    rebuild_key = Variable.get('rebuild_key', default_var='')
    url = Variable.get('api_url', default_var='')
    headers = {"Content-Type": "application/json"}
    data = {"rebuild_key": rebuild_key}

    response = requests.post(f'{url}/api/server/rebuild', headers=headers, json=data, timeout=900)  # 타임아웃 15분 설정

    if response.status_code != 200:
        raise ValueError(f"Request failed with status {response.status_code}: {response.text}")


with DAG(
    dag_id="dags_server_rebuild",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['server'],
) as dag:
    server_rebuild_task = PythonOperator(
        task_id='server_rebuild',
        python_callable=trigger_server_rebuild,
        dag=dag,
    )

    server_rebuild_task

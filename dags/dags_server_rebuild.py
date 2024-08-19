import json
from airflow import DAG
import datetime
import pendulum
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.models import Variable


with DAG(
    dag_id="dags_server_rebuild",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['server'],
) as dag:

    rebuild_key = Variable.get('rebuild_key', default_var='')

    server_rebuild_task = SimpleHttpOperator(
        task_id='server_rebuild',
        http_conn_id='tkl_web',
        endpoint='api/server/rebuild',
        method='POST',
        data=json.dumps({"rebuild_key": rebuild_key}),
        headers={"Content-Type": "application/json"},
        timeout=900,
        dag=dag,
    )

    server_rebuild_task

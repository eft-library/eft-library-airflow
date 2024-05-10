from airflow import DAG
from airflow.decorators import task
import datetime
import pendulum

with DAG(
    dag_id="dags_python_show_templates",
    schedule="30 9 * * *",
    start_date=pendulum.datetime(2024, 4, 10, tz="Asia/Seoul"),
    catchup=True, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['test'],
) as dag:

    @task(task_id='python_task')
    def show_templates(**kwargs):
        from pprint import pprint
        pprint(kwargs)

    show_templates()

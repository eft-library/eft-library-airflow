from airflow import DAG
from airflow.operators.bash import BashOperator
import datetime
import pendulum
from custom_module.data_dump_function import return_script

with DAG(
    dag_id="dags_data_dump",
    schedule="0 15 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['postgresql', "data_dump"],
) as dag:
    data_dump_task = BashOperator(
        task_id="data_dump",
        bash_command=return_script(),
    )

    data_dump_task
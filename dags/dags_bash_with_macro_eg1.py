from airflow import DAG
from airflow.operators.bash import BashOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_bash_with_macro_eg1",
    schedule="10 0 L * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['example'],
) as dag:

    bash_task_1 = BashOperator(
        task_id='bash_task_1',
        env={
            'START_DATE': '{{ data_interval_start.in_timezone("Asia/Seoul") | ds }}',
            'END_DATE': '{{ (data_interval_end.in_timezone("Asia/Seoul") - macros.dateutil.relativedelta.relativedelta(days=1)) | ds }}'
        },
        bash_command='echo "START_DATE: $START_DATE" && echo "END_DATE: $END_DATE"'
    )
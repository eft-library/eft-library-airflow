from airflow import DAG
from airflow.operators.bash import BashOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_bash_operator",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['example', "example2"],
    params={"example_key": "example_value"},
) as dag:
    bash_t1 = BashOperator(
        task_id="bash_t1", # 화면에 나오는 값
        bash_command="echo whoami",
    )
    bash_t2 = BashOperator(
        task_id="bash_t2", # 화면에 나오는 값
        bash_command="echo $HOSTNAME",
    )

    bash_t1 >> bash_t2
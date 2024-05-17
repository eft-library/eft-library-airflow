from airflow import DAG
from airflow.operators.bash import BashOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_bash_select_fruit",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['test'],
) as dag:

    t1_orange = BashOperator(
        task_id="t1_orange",
        bash_command="/home/airflow/plugins/shell/select_fruit.sh ORANGE"
    )

    t2_grape = BashOperator(
        task_id="t2_grape",
        bash_command="/home/airflow/plugins/shell/select_fruit.sh GRAPE"
    )

    t3_apple = BashOperator(
        task_id="t3_apple",
        bash_command="/home/airflow/plugins/shell/select_fruit.sh APPLE"
    )

    t4_melon = BashOperator(
        task_id="t1_melon",
        bash_command="/home/airflow/plugins/shell/select_fruit.sh MELON"
    )

    t1_orange >> t2_grape >> t3_apple >> t4_melon
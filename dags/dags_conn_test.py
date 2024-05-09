from airflow import DAG
from airflow.operators.empty import EmptyOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_conn_test",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['test'],
) as dag:
    t1 = EmptyOperator(
        task_id="t1", # 화면에 나오는 값
    )
    t2 = EmptyOperator(
        task_id="t2",
    )
    t3 = EmptyOperator(
        task_id="t3",
    )
    t4 = EmptyOperator(
        task_id="t4",
    )
    t5 = EmptyOperator(
        task_id="t5",
    )
    t6 = EmptyOperator(
        task_id="t6",
    )
    t7 = EmptyOperator(
        task_id="t7",
    )
    t8 = EmptyOperator(
        task_id="t8",
    )

    t1 >> [t2, t3] >> t4
    t5 >> t4
    [t4, t7] >> t6 >> t8
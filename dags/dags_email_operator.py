from airflow import DAG
from airflow.operators.email import EmailOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_email_operator",
    schedule="0 10 * * *",
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['test'],
) as dag:
    send_email_task = EmailOperator(
        task_id="send_email_task",
        to="poeynus@gmail.com",
        subject="Airflow 정기 이메일",
        html_content="Airflow 주기적인 스케줄링 완료"
    )
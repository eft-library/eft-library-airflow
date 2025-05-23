from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import os

default_args = {
    "owner": "airflow",
    "email_on_failure": False,
    "retries": 0,
}

dag = DAG(
    dag_id="dags_health_check",
    default_args=default_args,
    schedule_interval="*/5 * * * *",
    start_date=days_ago(1),
    catchup=False,
)

log_path = "/opt/airflow/health_check/logs/health_check.log"

# 1. health_check.sh 실행
run_health_check = BashOperator(
    task_id="run_health_check",
    bash_command="/opt/airflow/health_check/health_check.sh",
    dag=dag,
)


# 2. log를 읽어서 html 형태로 변환
def prepare_email_content(**kwargs):
    if os.path.exists(log_path):
        with open(log_path) as f:
            lines = f.readlines()
            html_lines = "<br>".join(line.strip() for line in lines)
            kwargs["ti"].xcom_push(key="email_body", value=html_lines)


prepare_email_body = PythonOperator(
    task_id="prepare_email_body",
    python_callable=prepare_email_content,
    provide_context=True,
    dag=dag,
)


# 3. 로그에 FAIL이 있는지 확인
def should_send_email(**kwargs):
    if os.path.exists(log_path):
        with open(log_path) as f:
            if "FAIL" in f.read():
                return "send_email"
    return "no_action"


decide_to_email = BranchPythonOperator(
    task_id="decide_to_email",
    python_callable=should_send_email,
    provide_context=True,
    dag=dag,
)


# 4. EmailOperator - 로그 내용을 본문에 포함
def get_email_body(ti):
    return ti.xcom_pull(task_ids="prepare_email_body", key="email_body")


send_email = EmailOperator(
    task_id="send_email",
    to=["poeynus@gmail.com"],
    cc=["moonjipsa@gmail.com"],
    subject="🚨 EFT Library 서비스에 문제가 생겼습니다.",
    html_content="{{ task_instance.xcom_pull(task_ids='prepare_email_body', key='email_body') }}",
    dag=dag,
    conn_id="smtp_gmail",
)

# 5. 아무 것도 안함
no_action = EmptyOperator(
    task_id="no_action",
    dag=dag,
)

# DAG 흐름 설정
run_health_check >> prepare_email_body >> decide_to_email >> [send_email, no_action]

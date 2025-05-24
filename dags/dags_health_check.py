from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import os

log_path = "/opt/airflow/health_check/logs/health_check.log"

default_args = {
    "owner": "airflow",
    "email_on_failure": False,
    "retries": 0,
}

with DAG(
    dag_id="dags_health_check",
    default_args=default_args,
    schedule_interval="*/5 * * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["health", "monitoring"],
) as dag:

    # 1. health_check.sh 실행
    run_health_check = BashOperator(
        task_id="run_health_check",
        bash_command=r'bash /opt/airflow/health_check/health_check.sh',
    )

    # 2. 로그를 <pre>로 감싸서 XCom 저장
    def prepare_email_content(**kwargs):
        task_instance = kwargs["ti"]
        if os.path.exists(log_path):
            with open(log_path) as f:
                content = f.read()
                html_content = f"<pre>{content}</pre>"
                task_instance.xcom_push(key="email_body", value=html_content)

    prepare_email_body = PythonOperator(
        task_id="prepare_email_body",
        python_callable=prepare_email_content,
    )

    # 3. 로그에 FAIL이 있는지 판단하여 분기
    def should_send_email(**kwargs):
        if os.path.exists(log_path):
            with open(log_path) as f:
                if "FAIL" in f.read():
                    return "send_email"
        return "no_action"

    decide_to_email = BranchPythonOperator(
        task_id="decide_to_email",
        python_callable=should_send_email,
    )

    # 4. Email 전송
    send_email = EmailOperator(
        task_id="send_email",
        to=["poeynus@gmail.com"],
        cc=["moonjipsa@gmail.com", "jjy2mn@gmail.com"],
        subject="🚨 테스트용입니다. (이선엽)",
        html_content="{{ task_instance.xcom_pull(task_ids='prepare_email_body', key='email_body') }}",
        conn_id="smtp_gmail",
    )

    # 5. 아무 것도 안함
    no_action = EmptyOperator(task_id="no_action")

    # DAG 흐름 연결
    run_health_check >> prepare_email_body >> decide_to_email >> [send_email, no_action]

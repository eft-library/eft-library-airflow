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
        bash_command='bash /opt/airflow/health_check/health_check.sh',
    )

    # 2. 로그 내용 검사 (FAIL 포함 여부)
    def check_fail_in_log(**kwargs):
        if os.path.exists(log_path):
            with open(log_path) as f:
                content = f.read()
                if "FAIL" in content:
                    return "prepare_email_body"
        return "success_action"

    check_log_result = BranchPythonOperator(
        task_id="check_log_result",
        python_callable=check_fail_in_log,
    )

    # 3. 실패한 경우: 로그 내용을 읽어 XCom으로 전달
    def prepare_email_content(**kwargs):
        ti = kwargs["ti"]
        if os.path.exists(log_path):
            with open(log_path) as f:
                content = f.read()
                html_content = f"<pre>{content}</pre>"
                ti.xcom_push(key="email_body", value=html_content)

    prepare_email_body = PythonOperator(
        task_id="prepare_email_body",
        python_callable=prepare_email_content,
    )

    # 4. 이메일 전송 (FAIL이 있을 때만 실행됨)
    send_email = EmailOperator(
        task_id="send_email",
        to=["poeynus@gmail.com"],
        cc=["moonjipsa@gmail.com", "jjy2mn@gmail.com"],
        subject="🚨 테스트용입니다. (이선엽)",
        html_content="{{ task_instance.xcom_pull(task_ids='prepare_email_body', key='email_body') }}",
        conn_id="smtp_gmail",
    )

    # 5. 성공 시 아무 것도 안 함
    success_action = EmptyOperator(task_id="success_action")

    # DAG 연결
    run_health_check >> check_log_result
    check_log_result >> prepare_email_body >> send_email
    check_log_result >> success_action

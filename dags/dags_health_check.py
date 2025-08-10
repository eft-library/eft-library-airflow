from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
from custom_module.psql_func import read_sql
from airflow.operators.email import EmailOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
from datetime import datetime
import time
import os
import requests

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
        bash_command="""
        bash /opt/airflow/health_check/health_check.sh
        """,
    )

    def measure_response_time(postgres_conn_id, **kwargs):
        services = {
            "Next.js": "http://eftlibrary.com/health",
            "FastAPI": "http://back.eftlibrary.com/health",
        }

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("insert_response_time.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                for service_name, url in services.items():
                    start = time.time()
                    try:
                        r = requests.get(url, timeout=10)
                        elapsed = time.time() - start
                    except Exception:
                        elapsed = None  # 실패 시 NULL 처리

                    cursor.execute(sql, (service_name, elapsed, datetime.now()))
            conn.commit()

    def save_health_check(postgres_conn_id, **kwargs):
        if not os.path.exists(log_path):
            return

        postgres_hook = PostgresHook(postgres_conn_id)
        sql = read_sql("insert_health_check.sql")

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                with open(log_path, "r") as f:
                    for line in f:
                        if not line.strip():
                            continue

                        print(line)
                        try:
                            parts = line.strip().split("] ")
                            timestamp_str = parts[0].strip("[")
                            log_body = parts[1]
                            service_name, status = log_body.split(": ")
                            checked_at = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )

                            cursor.execute(
                                sql, (service_name.strip(), status.strip(), checked_at)
                            )
                        except Exception as e:
                            # 에러 로깅 (옵션)
                            print(f"Error parsing line: {line} -> {e}")

                conn.commit()

    # 2. 로그 내용 검사 (FAIL 포함 여부)
    def check_fail_in_log(**kwargs):
        if os.path.exists(log_path):
            with open(log_path) as f:
                content = f.read()
                if "FAIL" in content:
                    return "prepare_email_body"
        return "success_action"

    # 3. 실패한 경우: 로그 내용을 읽어 XCom으로 전달
    def prepare_email_content(**kwargs):
        ti = kwargs["ti"]
        if os.path.exists(log_path):
            with open(log_path) as f:
                content = f.read()
                html_content = f"<pre>{content}</pre>"
                ti.xcom_push(key="email_body", value=html_content)

    check_log_result = BranchPythonOperator(
        task_id="check_log_result",
        python_callable=check_fail_in_log,
    )

    save_to_postgres = PythonOperator(
        task_id="save_to_postgres",
        python_callable=save_health_check,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    prepare_email_body = PythonOperator(
        task_id="prepare_email_body",
        python_callable=prepare_email_content,
    )

    measure_response_time_task = PythonOperator(
        task_id="measure_response_time",
        python_callable=measure_response_time,
        op_kwargs={"postgres_conn_id": "tkl_db"},
    )

    # 4. 이메일 전송 (FAIL이 있을 때만 실행됨)
    send_email = EmailOperator(
        task_id="send_email",
        to=["poeynus@gmail.com"],
        cc=["moonjipsa@gmail.com", "jjy2mn@gmail.com"],
        subject="🚨 EFT Library 서비스에 문제가 생겼습니다.",
        html_content="{{ task_instance.xcom_pull(task_ids='prepare_email_body', key='email_body') }}",
        conn_id="smtp_gmail",
    )

    # 5. 성공 시 아무 것도 안 함
    success_action = EmptyOperator(task_id="success_action")

    # DAG 연결
    (
        run_health_check
        >> save_to_postgres
        >> measure_response_time_task
        >> check_log_result
    )
    check_log_result >> prepare_email_body >> send_email
    check_log_result >> success_action

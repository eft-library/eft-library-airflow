"""DAG 최종 실패 메일 및 정리 작업에 의한 실패 상태 누락 방지."""

from html import escape

from airflow.exceptions import AirflowException
from airflow.providers.smtp.hooks.smtp import SmtpHook
from airflow.providers.standard.operators.python import PythonOperator


def send_dag_failure_email(context):
    """태스크 재시도가 끝나고 DAG가 실패했을 때 호출한다."""
    dag_run = context["dag_run"]
    dag_id = dag_run.dag_id
    # Airflow 3.1의 DAG callback에 전달되는 ti는 실패 태스크가 아닐 수 있다.
    details = {
        "DAG": dag_id,
        "Run ID": dag_run.run_id,
        "시작 시간": getattr(dag_run, "start_date", None),
        "종료 시간": getattr(dag_run, "end_date", None),
        "실패 사유": context.get("reason") or "task_failure",
    }
    rows = "".join(
        f"<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>"
        for label, value in details.items()
    )
    with SmtpHook(smtp_conn_id="smtp_gmail") as smtp:
        smtp.send_email_smtp(
            to=["poeynus@gmail.com", "moonjipsa@gmail.com"],
            from_email="poeynus@gmail.com",
            subject=f"[EFT Library] DAG 실행 실패: {dag_id}",
            html_content=(
                "<h2>DAG 실행이 실패했습니다.</h2>"
                f"<table>{rows}</table>"
                "<p>Airflow에서 해당 실행의 실패 태스크 로그를 확인해 주세요.</p>"
            ),
        )


def fail_on_upstream_error():
    raise AirflowException("상위 태스크가 실패했습니다. 해당 태스크 로그를 확인하세요.")


def add_failure_watcher(dag):
    """모든 기존 태스크를 감시하여 ALL_DONE 정리 작업도 실패를 가리지 않게 한다."""
    tasks = list(dag.tasks)
    watcher = PythonOperator(
        task_id="watch_dag_failure",
        python_callable=fail_on_upstream_error,
        trigger_rule="one_failed",
        retries=0,
        email_on_failure=False,
        email_on_retry=False,
        dag=dag,
    )
    for task in tasks:
        task >> watcher

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.email import EmailOperator
from airflow.operators.dummy import DummyOperator
import datetime
import pendulum
from custom_module.data_dump_func import dump_script, remove_old_file_script, get_today


def choose_branch(**kwargs):
    task_instance = kwargs["ti"]
    bash_return_code = task_instance.xcom_pull(task_ids="data_dump")
    if bash_return_code == "0":
        return "success_task"
    else:
        return "failure_task"


today = get_today()
backup_file_path = f"/opt/airflow/latest_data/{today}_backup.sql"

with DAG(
    dag_id="dags_data_dump",
    schedule="50 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["postgresql", "data_dump"],
) as dag:

    data_dump_task = BashOperator(
        task_id="data_dump",
        bash_command=dump_script(),
        do_xcom_push=True,
    )

    branch_task = BranchPythonOperator(
        task_id="branch_task",
        python_callable=choose_branch,
    )

    success_task = BashOperator(
        task_id="success_task",
        bash_command=remove_old_file_script(),
    )

    send_email = EmailOperator(
        task_id="send_email",
        to=["poeynus@gmail.com"],
        cc=["moonjipsa@gmail.com"],
        # subject=f"✅ {today} PostgreSQL 데이터 Dump 완료",
        subject=f"메일 전송 테스트",
        html_content=f"<p>{today} 백업 파일이 성공적으로 생성되어 첨부되었습니다.</p>",
        # files=[backup_file_path],
    )

    failure_task = DummyOperator(task_id="failure_task")

    data_dump_task >> branch_task
    branch_task >> success_task >> send_email
    branch_task >> failure_task

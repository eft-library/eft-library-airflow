from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import BranchPythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator
import datetime
import pendulum
from custom_module.data_dump_func import (
    dump_script,
    remove_old_file_script,
    get_today,
    compress_backup_script,
)


def choose_branch(**kwargs):
    code = kwargs["ti"].xcom_pull(task_ids="data_dump")
    if code and code.strip() == "0":
        return "compress_backup"
    return "failure_task"



today = get_today()
backup_file_path = f"/opt/airflow/latest_data/{today}_backup.sql"
compressed_file_path = f"{backup_file_path}.gz"

with DAG(
    dag_id="dags_data_dump",
    schedule="0 0 * * *",
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

    compress_backup = BashOperator(
        task_id="compress_backup",
        bash_command=compress_backup_script(backup_file_path),
    )

    success_task = BashOperator(
        task_id="success_task",
        bash_command=remove_old_file_script(),
    )

    failure_task = EmptyOperator(task_id="failure_task")

    # DAG 흐름 정의
    data_dump_task >> branch_task
    branch_task >> compress_backup >> success_task
    branch_task >> failure_task

from airflow import DAG
from custom_module.dag_failure_alert import add_failure_watcher, send_dag_failure_email
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import BranchPythonOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.transfers.local_to_s3 import LocalFilesystemToS3Operator
import datetime
import pendulum
from custom_module.data_dump_func import (
    dump_script,
    remove_old_file_script,
    compress_backup_script,
)


def choose_branch(**kwargs):
    code = kwargs["ti"].xcom_pull(task_ids="data_dump")
    if code and code.strip() == "0":
        return "compress_backup"
    return "failure_task"



today = "{{ dag_run.start_date.in_timezone('Asia/Seoul').strftime('%Y_%m_%d') }}"
backup_file_path = f"/opt/airflow/latest_data/{today}_backup.sql"
compressed_file_path = f"{backup_file_path}.gz"

with DAG(
    on_failure_callback=send_dag_failure_email,
    dag_id="dags_data_dump",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=["postgresql", "data_dump"],
) as dag:

    data_dump_task = BashOperator(
        task_id="data_dump",
        bash_command=dump_script(backup_file_path),
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

    upload_to_rustfs = LocalFilesystemToS3Operator(
        task_id="upload_to_rustfs",
        filename=compressed_file_path,
        dest_key=f"{today}_backup.sql.gz",
        dest_bucket="postgresql",
        aws_conn_id="rustfs_storage",
        replace=True,
        retries=2,
        retry_delay=datetime.timedelta(minutes=1),
    )

    success_task = BashOperator(
        task_id="success_task",
        bash_command=remove_old_file_script(),
    )

    failure_task = EmptyOperator(task_id="failure_task")

    # DAG 흐름 정의
    data_dump_task >> branch_task
    branch_task >> compress_backup >> upload_to_rustfs >> success_task
    branch_task >> failure_task

add_failure_watcher(dag)

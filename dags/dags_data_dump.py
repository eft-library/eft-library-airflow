from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import (
    BranchPythonOperator,
    PythonOperator,
)
from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import datetime
import hashlib
import os
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
minio_bucket_name = "eftlibrary"
minio_object_key = f"data-dump/{today}_backup.sql.gz"


def upload_backup_to_minio():
    local_size = os.path.getsize(compressed_file_path)
    sha256 = hashlib.sha256()
    with open(compressed_file_path, "rb") as backup_file:
        for chunk in iter(lambda: backup_file.read(1024 * 1024), b""):
            sha256.update(chunk)

    hook = S3Hook(aws_conn_id="minio_s3")
    if not hook.check_for_bucket(minio_bucket_name):
        raise ValueError(f"MinIO bucket does not exist: {minio_bucket_name}")

    hook.load_file(
        filename=compressed_file_path,
        key=minio_object_key,
        bucket_name=minio_bucket_name,
        replace=True,
    )

    uploaded = hook.get_conn().head_object(
        Bucket=minio_bucket_name,
        Key=minio_object_key,
    )
    uploaded_size = uploaded["ContentLength"]
    if uploaded_size != local_size:
        raise ValueError(
            "MinIO upload size mismatch: "
            f"local={local_size}, uploaded={uploaded_size}"
        )

    return {
        "bucket": minio_bucket_name,
        "key": minio_object_key,
        "size_bytes": uploaded_size,
        "size_mb": round(uploaded_size / 1024 / 1024, 2),
        "sha256": sha256.hexdigest(),
    }

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

    upload_backup = PythonOperator(
        task_id="upload_backup_to_minio",
        python_callable=upload_backup_to_minio,
    )

    success_task = BashOperator(
        task_id="success_task",
        bash_command=remove_old_file_script(),
    )

    send_email = EmailOperator(
        task_id="send_email",
        to=["poeynus@gmail.com", "moonjipsa@gmail.com"],
        subject=f"✅ {today} PostgreSQL 데이터 Dump 완료",
        html_content="""
            <p>PostgreSQL 데이터 Dump가 생성되어 MinIO에 업로드되었습니다.</p>
            <ul>
                <li>Bucket: {{ ti.xcom_pull(task_ids='upload_backup_to_minio')['bucket'] }}</li>
                <li>Object: {{ ti.xcom_pull(task_ids='upload_backup_to_minio')['key'] }}</li>
                <li>Size: {{ ti.xcom_pull(task_ids='upload_backup_to_minio')['size_mb'] }} MB</li>
                <li>SHA-256: {{ ti.xcom_pull(task_ids='upload_backup_to_minio')['sha256'] }}</li>
            </ul>
        """,
        conn_id="smtp_gmail",
        from_email="poeynus@gmail.com",
    )

    failure_task = EmptyOperator(task_id="failure_task")

    # DAG 흐름 정의
    data_dump_task >> branch_task
    branch_task >> compress_backup >> upload_backup >> success_task >> send_email
    branch_task >> failure_task

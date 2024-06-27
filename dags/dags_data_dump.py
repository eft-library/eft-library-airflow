from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.dummy import DummyOperator
import datetime
import pendulum
from custom_module.data_dump_function import dump_script, remove_old_file_script

# xcom으로 data_dump_task 성공 여부를 가져옴
def choose_branch(**kwargs):
    task_instance = kwargs['ti']
    bash_return_code = task_instance.xcom_pull(task_ids='data_dump')
    if bash_return_code == '0':
        return 'success_task'
    else:
        return 'failure_task'


with DAG(
    dag_id="dags_data_dump",
    schedule="0 15 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['postgresql', "data_dump"],
) as dag:
    data_dump_task = BashOperator(
        task_id="data_dump",
        bash_command=dump_script(),
        do_xcom_push=True,
    )

    branch_task = BranchPythonOperator(
        task_id='branch_task',
        python_callable=choose_branch,
        provide_context=True,
    )

    success_task = BashOperator(
        task_id='success_task',
        bash_command=remove_old_file_script(),
    )

    failure_task = DummyOperator(
        task_id='failure_task',
    )

    data_dump_task >> branch_task >> [success_task, failure_task]

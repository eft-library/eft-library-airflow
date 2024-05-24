from airflow import DAG
import pendulum
from airflow.decorators import task

with DAG(
    dag_id="dags_python_with_xcom_eg2",
    schedule="10 0 * * *",
    start_date=pendulum.datetime(2024, 3, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:
    @task(task_id='python_xcom_push_by_return')
    def xcom_push_result(**kwargs):
        return 'success'

    @task(task_id='python_xcom_pull_task2')
    def xcom_pull1(**kwargs):
        ti = kwargs['ti']
        value1 = ti.xcom_pull(task_ids='python_xcom_push_by_return')
        print(value1)

    @task(task_id='python_xcom_pull_task2')
    def xcom_pull2(status, **kwargs):
        print(status)

    python_xcom_push_by_return = xcom_push_result()
    xcom_pull2(python_xcom_push_by_return)

    python_xcom_push_by_return >> xcom_pull1()
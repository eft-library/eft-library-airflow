from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator
import datetime
import pendulum

with DAG(
    dag_id="dags_python_template",
    schedule="30 9 * * *",
    start_date=pendulum.datetime(2024, 4, 10, tz="Asia/Seoul"),
    catchup=False, # True이면 start_data부터 지금까지 누락된 날짜의 스케줄이 한 번에 돌게 된다.
    dagrun_timeout=datetime.timedelta(minutes=60),
    tags=['test'],
) as dag:
    def python_function(start_date, end_date, **kwargs):
        print(start_date)
        print(end_date)

    python_t1 = PythonOperator(
        task_id='python_t1',
        python_callable=python_function,
        op_kwargs={'start_date': '{{data_interval_start | ds}}', 'end_date': '{{data_interval_end | ds}}'}
    )

    @task(task_id='python_t2')
    def python_function2(name, **kwargs):
        print(name)
        print(kwargs)
        print(kwargs['ds'])
        print(kwargs['ts'])
        print(str(kwargs['data_interval_start']))
        print(str(kwargs['data_interval_end']))
        print(str(kwargs['ti']))

    python_t1 >> python_function2(name='hi')
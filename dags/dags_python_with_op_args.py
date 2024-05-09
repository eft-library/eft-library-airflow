from airflow import DAG
from airflow.operators.python import PythonOperator
import datetime
import pendulum

with DAG(
    dag_id='dags_python_with_op_args',
    schedule='30 6 * * *',
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:

    def regist(name, sex, *args):
        print(name)
        print(sex)
        print(args)

    regist_t1 = PythonOperator(
        task_id='regist_t1',
        python_callable=regist,
        op_args=['me', 'po', 'ey', 'nus']
    )

    regist_t1
from airflow import DAG
from airflow.operators.python import PythonOperator
import datetime
import pendulum

with DAG(
    dag_id='dags_python_with_op_kwargs',
    schedule='30 6 * * *',
    start_date=pendulum.datetime(2021, 1, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:

    def regist2(name, sex, *args, **kwargs):
        print(name)
        print(sex)
        print(args)
        email = kwargs['email'] or None
        phone = kwargs['phone'] or None
        if email:
            print(email)
        if phone:
            print(phone)

    regist2_t1 = PythonOperator(
        task_id='regist2_t1',
        python_callable=regist2,
        op_args=['me', 'po', 'ey', 'nus'],
        op_kwargs={'email': '<EMAIL>', 'phone': '555-555-5555'}
    )

    regist2_t1
from airflow import DAG
import pendulum
from airflow.operators.python import PythonOperator

# 이거 insert로 바꾸고 조회 쿼리도 최근 limit 1로 수정 해야 함
with DAG(
        dag_id='dags_tkw_youtube_update',
        start_date=pendulum.datetime(2024, 5, 1, tz='Asia/Seoul'),
        schedule=None,
        catchup=False
) as dag:
    def update_youtube(postgres_conn_id, **kwargs):
        from airflow.providers.postgres.hooks.postgres import PostgresHook
        from contextlib import closing

        postgres_hook = PostgresHook(postgres_conn_id)
        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                sql = """
                update tkw_youtube
                set youtube_id = %s, youtube_update_time = %s
                where youtube_id = 'MKYOspIJiWE';
                """
                cursor.execute(sql, ('MKYOspIJiWE', pendulum.now('Asia/Seoul')))
                conn.commit()


    update_tkw_youtube = PythonOperator(
        task_id='update_tkw_youtube',
        python_callable=update_youtube,
        op_kwargs={'postgres_conn_id': 'tkw_db'}
    )
    update_tkw_youtube

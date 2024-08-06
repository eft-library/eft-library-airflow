import json
from airflow import DAG
from airflow.providers.http.operators.http import HttpOperator
from airflow.decorators import task
import pendulum


with DAG(
    dag_id='dags_simple_http_operator',
    start_date=pendulum.datetime(2023, 4, 1, tz='Asia/Seoul'),
    catchup=False,
    schedule=None
) as dag:
    new_query = """
    {
       items {
        name
        shortName
            image512pxLink
            category {
              name
              parent {
                name
              }
            }
            properties {
                  __typename
                  ... on ItemPropertiesWeapon {
                caliber
                defaultAmmo {
                  name
                }
                fireModes
                fireRate
                defaultErgonomics
                defaultRecoilVertical
                defaultRecoilHorizontal
                }
              }
            }
    }
    """

    tarkov_weapon_info = HttpOperator(
        task_id='tarkov_weapon_info',
        http_conn_id='tarkov_dev',
        endpoint='/graphql',
        data=json.dumps({"query": new_query}),
        headers={"Content-Type": "application/json"},
        log_response=True
    )

    @task(task_id='print_data')
    def print_data(**kwargs):
        ti = kwargs['ti']
        result = ti.xcom_pull(task_ids='tarkov_weapon_info')
        from pprint import pprint

        pprint(json.loads(result))

    tarkov_weapon_info >> print_data()

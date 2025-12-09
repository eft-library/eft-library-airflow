from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from contextlib import closing
import pendulum
from custom_module.psql_func import read_sql

BATCH_SIZE = 500


@dag(
    dag_id="dags_item_detail_upsert",
    start_date=pendulum.datetime(2024, 5, 1, tz="Asia/Seoul"),
    schedule="50 0 * * *",
    catchup=False,
    max_active_tasks=10,
    default_args={
        "owner": "airflow",
        "retries": 1,
        "retry_delay": pendulum.duration(minutes=5),
    },
    tags=["postgresql", "tarkov-dev-api"],
)
def item_detail_upsert():

    @task
    def get_total_count(postgres_conn_id: str) -> int:
        hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_count.sql")
        with closing(hook.get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute(sql)
            return cur.fetchone()[0]

    @task
    def make_ranges(total_count: int) -> list[dict]:
        """
        XCom(리스트) → process_batch 에 매핑됨.
        각 dict가 하나의 Task 인스턴스(Worker Slot)를 생성.
        """
        return [
            {"start": start, "end": min(start + BATCH_SIZE, total_count)}
            for start in range(0, total_count, BATCH_SIZE)
        ]

    @task
    def process_batch(batch: dict, postgres_conn_id: str):
        start, end = batch["start"], batch["end"]
        hook = PostgresHook(postgres_conn_id)
        sql = read_sql("item_detail_upsert.sql")
        with closing(hook.get_conn()) as conn, closing(conn.cursor()) as cur:
            cur.execute(sql, (start, end))
            conn.commit()

    total = get_total_count(postgres_conn_id="tkl_db")
    ranges = make_ranges(total)
    process_batch.expand(batch=ranges, postgres_conn_id=["tkl_db"])


dag = item_detail_upsert()

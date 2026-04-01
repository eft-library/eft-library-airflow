from contextlib import closing

import pendulum
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.standard.operators.python import PythonOperator


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": pendulum.duration(minutes=5),
}


AUTOCOMPLETE_SQL = """
INSERT INTO autocomplete_items (autocomplete_text_en, autocomplete_text_ko, autocomplete_text_ja, url, category,
                                sort_order)
SELECT autocomplete_text_en,
       autocomplete_text_ko,
       autocomplete_text_ja,
       url,
       category,
       rn AS sort_order
FROM (SELECT autocomplete_text_en,
             autocomplete_text_ko,
             autocomplete_text_ja,
             url,
             category,
             ROW_NUMBER() OVER (ORDER BY category, sort_order) AS rn
      FROM (SELECT 'Tarkov Maps: ' || name_en           AS autocomplete_text_en,
                   '타르코프 지도: ' || name_ko               AS autocomplete_text_ko,
                   'Tarkov マップ: ' || name_ja         AS autocomplete_text_ja,
                   '/map-of-tarkov/' || normalized_name AS url,
                   'MAP_OF_TARKOV'                      AS category,
                   sort_order
            FROM maps
            UNION ALL
            SELECT 'Interactive Maps: ' || name_en        AS autocomplete_text_en,
                   '타르코프 지도: ' || name_ko                 AS autocomplete_text_ko,
                   'インタラクティブ マップ: ' || name_ja AS autocomplete_text_ja,
                   '/map/' || normalized_name             AS url,
                   'MAP'                                  AS category,
                   sort_order
            FROM maps
            UNION ALL
            SELECT 'Boss: ' || name_en         AS autocomplete_text_en,
                   '보스: ' || name_ko           AS autocomplete_text_ko,
                   'ボス: ' || name_ja         AS autocomplete_text_ja,
                   '/boss/' || normalized_name AS url,
                   'BOSS'                      AS category,
                   sort_order
            FROM bosses
            WHERE is_boss = true
            UNION ALL
            SELECT 'Quests: ' || name_en               AS autocomplete_text_en,
                   '퀘스트: ' || name_ko                  AS autocomplete_text_ko,
                   'クエスト: ' || name_ja             AS autocomplete_text_ja,
                   '/quest/detail/' || normalized_name AS url,
                   'QUEST'                             AS category,
                   sort_order
            FROM quests
            UNION ALL
            SELECT 'Trader: ' || name_en        AS autocomplete_text_en,
                   '상인: ' || name_ko            AS autocomplete_text_ko,
                   '商人: ' || name_ja          AS autocomplete_text_ja,
                   '/quest/' || normalized_name AS url,
                   'TRADER'                     AS category,
                   sort_order
            FROM traders
            WHERE is_use = true
            UNION ALL
            SELECT 'Item: ' || name_en              AS autocomplete_text_en,
                   '아이템: ' || name_ko               AS autocomplete_text_ko,
                   'アイテム: ' || name_ja          AS autocomplete_text_ja,
                   '/item/info/' || normalized_name AS url,
                   'ITEM'                           AS category,
                   0
            FROM items) AS base) AS numbered
ORDER BY rn
ON CONFLICT (url)
    DO UPDATE SET autocomplete_text_en = EXCLUDED.autocomplete_text_en,
                  autocomplete_text_ko = EXCLUDED.autocomplete_text_ko,
                  autocomplete_text_ja = EXCLUDED.autocomplete_text_ja,
                  category             = EXCLUDED.category,
                  update_time          = NOW();
"""


with DAG(
    dag_id="v3_dags_autocomplete",
    default_args=default_args,
    start_date=pendulum.datetime(2026, 3, 1, tz="Asia/Seoul"),
    schedule="17 0 * * *",
    tags=["postgresql", "tarkov-dev-api"],
    catchup=False,
) as dag:

    def update_autocomplete(postgres_conn_id):
        postgres_hook = PostgresHook(postgres_conn_id)

        with closing(postgres_hook.get_conn()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute(AUTOCOMPLETE_SQL)
            conn.commit()

    update_autocomplete_task = PythonOperator(
        task_id="update_autocomplete",
        python_callable=update_autocomplete,
        op_kwargs={"postgres_conn_id": "platform_db"},
    )

    update_autocomplete_task

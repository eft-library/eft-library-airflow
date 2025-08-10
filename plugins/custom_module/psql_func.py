sql_home_path = "/opt/airflow/eft-library-airflow/plugins/delete_issue_posts.sql/"


def read_sql(sql_path):
    with open(sql_home_path + sql_path, "r") as file:
        sql_query = file.read()
        return sql_query

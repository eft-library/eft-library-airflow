
sql_home_path = '/home/airflow/plugins/sql/'

def read_sql(sql_path):
    with open(sql_home_path + sql_path, 'r') as file:
        sql_query = file.read()
        return sql_query
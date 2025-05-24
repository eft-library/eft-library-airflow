def health_check_script():

    return """
        bash /opt/airflow/health_check/health_check.sh
        """
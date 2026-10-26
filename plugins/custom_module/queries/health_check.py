"""SQL for health check. Execution and transactions belong to the caller."""


INSERT_RESPONSE_TIME_SQL = """
INSERT INTO response_time (service_name, response_ms, checked_time)
VALUES (%s, %s, %s);
"""


INSERT_HEALTH_CHECK_SQL = """
INSERT INTO health_check (service_name, status, checked_time)
VALUES (%s, %s, %s);
"""

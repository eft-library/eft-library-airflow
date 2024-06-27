#!/bin/bash

git pull origin main

source airflow_venv/bin/activate

# Airflow Web Server 종료
pkill -f "airflow webserver"
echo "Airflow Web Server를 종료"

# Airflow Scheduler 종료
pkill -f "airflow scheduler"
echo "Airflow Scheduler를 종료"

# 3초 딜레이
sleep 3

# Airflow Scheduler 다시 실행
nohup airflow scheduler > scheduler.log 2>&1 &

# Airflow Web Server 다시 실행
nohup airflow webserver > webserver.log 2>&1 &

echo "Airflow Scheduler와 Web Server를 다시 실행했습니다."

deactivate
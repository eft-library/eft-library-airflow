#!/bin/bash

LOG_FILE="/opt/airflow/health_check/logs/health_check.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

rm -f "$LOG_FILE"

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

check_http() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null; then
        log "$name: OK"
    else
        log "$name: FAIL"
    fi
}

check_postgres() {
    if PGPASSWORD=TKL0717 psql -U tkl -h 192.168.219.102 -p 13245 -d prd -c "SELECT 1;" > /dev/null 2>&1; then
        log "PostgreSQL: OK"
    else
        log "PostgreSQL: FAIL"
    fi
}

check_kafka_topic() {
    local BROKER="192.168.219.102:9092"
    local TOPIC="web-logs-topic"

    if kcat -b "$BROKER" -L 2>/dev/null | grep -q "topic \"$TOPIC\""; then
        log "Kafka topic '${TOPIC}': OK"
        return 0
    else
        log "Kafka topic '${TOPIC}': FAIL"
        return 1
    fi
}

check_airflow_health() {
    local url="http://localhost:8080/health"
    if curl -sf "$url" | jq -e '.metadatabase.status == "healthy" and .scheduler.status == "healthy"' > 2>/dev/null; then
        log "Airflow API Health: OK"
    else
        log "Airflow API Health: FAIL"
    fi
}

check_npm_health() {
    local url="http://192.168.219.102:81"
    if curl -sf "$url" > /dev/null; then
        log "Nginx Proxy Manager Health: OK"
    else
        log "Nginx Proxy Manager Health: FAIL"
    fi
}

### 실행 부분 ###
check_http "Next.js" "http://192.168.219.102:4002/api/health"
check_http "FastAPI" "http://192.168.219.102:9022/api/news/health"
check_http "MinIO" "http://192.168.219.102:9000/minio/health/live"

check_postgres
check_kafka_topic
check_airflow_health
check_npm_health
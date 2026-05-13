#!/bin/bash

# =========================
# 기본 설정
# =========================
LOG_FILE="/opt/airflow/latest_data/health_check.log"
TIMEOUT=5

# 로그 초기화
: > "$LOG_FILE"

# =========================
# 로그 함수
# =========================
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check() {
  local name="$1"
  local cmd="$2"

  if timeout ${TIMEOUT}s bash -c "$cmd" >/dev/null 2>&1; then
    log "✅ [OK]   ${name}"
  else
    log "❌ [FAIL] ${name}"
  fi
}

log "==================== Health Check Start ===================="

# =========================
# HTTP 서비스
# =========================
check "FastAPI" \
  "curl -sf http://172.30.1.100:9022/api/news/health"

check "NextJS" \
  "curl -sf http://172.30.1.100:4002/api/health"

check "MinIO" \
  "curl -sf http://172.30.1.100:9000/minio/health/live"

# =========================
# TCP 서비스
# =========================
check "Redis" \
  "nc -z 172.30.1.100 6379"

check "Kafka" \
  "nc -z 172.30.1.100 9092"

# =========================
# Database
# =========================
check "PostgreSQL" \
  "psql -U tkl -h 172.30.1.100 -p 13245 -d platform_db -c 'SELECT 1;'"

# =========================
# Docker 내부 서비스
# =========================
check "Nginx Proxy Manager" \
  "curl -sf http://npm:81"

check "Airflow API Server" \
  "curl -sf http://airflow-airflow-apiserver-1:8080/api/v2/monitor/health"

log "==================== Health Check End ======================"
echo "" >> "$LOG_FILE"

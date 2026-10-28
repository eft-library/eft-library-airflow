"""AIOps HTTP orchestration. Analysis retries remain in the server's DB queue."""

import json
import logging
import time

import requests

log = logging.getLogger(__name__)
TRANSIENT_HTTP = {409, 429, 500, 502, 503, 504}


class AIOpsAPIError(RuntimeError):
    def __init__(self, status_code):
        self.status_code = status_code
        # Do not include request headers or potentially sensitive response bodies.
        super().__init__(f"AIOps API HTTP {status_code}")


class AIOpsStreamInterrupted(RuntimeError):
    """The stream ended without a trustworthy final event; recheck the DB job."""


class AIOpsClient:
    def __init__(self, base_url, token, worker_timeout=900):
        if not token:
            raise ValueError("Airflow Variable AIOPS_API_TOKEN에 API 키를 설정하세요.")
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-AIOps-Key": token}
        self.worker_timeout = worker_timeout

    def request(self, method, path, *, body=None, worker=False):
        response = requests.request(
            method, self.base_url + path, headers=self.headers, json=body,
            timeout=(10, self.worker_timeout if worker else 120),
        )
        if not response.ok:
            raise AIOpsAPIError(response.status_code)
        return response.json()

    def run_worker_stream(self):
        started = time.monotonic()
        final_job = None
        stream_error = False
        with requests.post(
            self.base_url + "/v1/worker/run-once/stream",
            headers=self.headers, stream=True, timeout=(10, 45),
        ) as response:
            if not response.ok:
                raise AIOpsAPIError(response.status_code)
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip() != "text/event-stream":
                raise AIOpsStreamInterrupted("Unexpected Worker stream content type")
            response.encoding = "utf-8"
            for line in response.iter_lines(chunk_size=1, decode_unicode=True):
                if time.monotonic() - started > self.worker_timeout:
                    raise AIOpsStreamInterrupted("Worker stream exceeded configured time limit")
                if not line or not line.startswith("data:"):
                    continue
                try:
                    event = json.loads(line[5:].lstrip())
                except (ValueError, TypeError):
                    raise AIOpsStreamInterrupted("Invalid Worker stream JSON") from None
                if not isinstance(event, dict):
                    raise AIOpsStreamInterrupted("Invalid Worker stream event")
                name = event.get("event")
                job_id = event.get("job_id")
                if name == "codex.message":
                    log.info("Codex [job=%s]: %s", job_id, event.get("message"))
                elif name == "worker.report":
                    log.info("AIOps report [job=%s severity=%s]: %s",
                             job_id, event.get("severity"), event.get("summary"))
                elif name == "codex.turn.completed":
                    log.info("Codex token usage [job=%s]: %s", job_id, event.get("usage", {}))
                elif name == "heartbeat":
                    log.info("AIOps heartbeat: job=%s elapsed=%ss", job_id, event.get("elapsed_seconds"))
                elif name == "worker.finished":
                    final_job = event.get("job")
                    if not isinstance(final_job, dict) or not final_job.get("status"):
                        raise AIOpsStreamInterrupted("Invalid Worker final job")
                    log.info("AIOps Worker finished: job=%s status=%s",
                             final_job.get("job_id"), final_job["status"])
                    if event.get("dropped_events"):
                        log.warning("AIOps stream dropped %s progress events", event["dropped_events"])
                elif name == "error":
                    log.warning("AIOps stream error: %s", event.get("error"))
                    stream_error = True
                elif name in {
                    "worker.started", "worker.claimed", "codex.thread.started",
                    "codex.turn.started", "codex.activity", "codex.report_candidate",
                    "codex.error", "worker.validating",
                }:
                    # Log only documented public fields, never raw events or HTTP headers.
                    log.info("AIOps event=%s job=%s", name, job_id)
        if final_job is None or stream_error:
            raise AIOpsStreamInterrupted("Worker stream ended without confirmed final status")
        return final_job

    def completed(self, job_id):
        job = self.request("GET", f"/v1/jobs/{job_id}")
        state = job["status"]
        log.info("AIOps target job=%s status=%s", job_id, state)
        if state == "COMPLETED":
            return True
        if state in {"FAILED", "TIMEOUT", "CANCELLED"}:
            raise RuntimeError(f"AIOps job {job_id}: {state} (error={job.get('error')})")
        if state not in {"PENDING", "RUNNING"}:
            raise RuntimeError(f"Unknown AIOps job status: {state}")
        return False

    def advance(self, job_id):
        """Each sensor poke checks the target, runs one queue item, then checks again."""
        try:
            if self.completed(job_id):
                return True
            # Also call for RUNNING: after an API restart the Worker recovers stale jobs.
            # A live Worker is protected by the server's DB lock (HTTP 409).
            self.run_worker_stream()
            return self.completed(job_id)
        except (requests.ConnectionError, requests.Timeout,
                requests.exceptions.ChunkedEncodingError, AIOpsStreamInterrupted):
            log.warning("AIOps connection interrupted; check the same job on the next poke")
            return False
        except AIOpsAPIError as exc:
            if exc.status_code not in TRANSIENT_HTTP:
                raise
            log.warning("AIOps HTTP %s; check the same job on the next poke", exc.status_code)
            return False


def get_client():
    from airflow.sdk import BaseHook, Variable

    connection = BaseHook.get_connection("aiops")
    extra = connection.extra_dejson
    base_url = extra.get("base_url", "http://172.30.1.100:9023")
    token = Variable.get("AIOPS_API_TOKEN")
    return AIOpsClient(base_url, token, float(extra.get("worker_timeout", 900)))


def _call(method, path, body=None):
    from airflow.exceptions import AirflowFailException

    try:
        return get_client().request(method, path, body=body)
    except AIOpsAPIError as exc:
        if exc.status_code not in TRANSIENT_HTTP:
            raise AirflowFailException(str(exc)) from None
        raise


def check_status():
    result = _call("GET", "/v1/status")
    if result.get("database", {}).get("status") != "ready":
        raise RuntimeError("AIOps database is not ready")


def collect():
    result = _call("POST", "/v1/collect", {})
    log.info("AIOps collection status=%s", result.get("status"))
    for service, coverage in result.get("coverage", {}).items():
        log.info("AIOps collection coverage service=%s: %s", service, coverage)
    log.info("AIOps collection database_registration=%s", result.get("database_registration"))
    if result.get("status") == "partial":
        log.warning("AIOps collection is partial; consult service coverage above")


def report_date(report_type, context):
    """Pin the closed period to the run boundary, including delayed executions."""
    import pendulum
    from datetime import date

    run = context["dag_run"]
    explicit_date = (run.conf or {}).get("date")
    if explicit_date:
        return date.fromisoformat(explicit_date).isoformat()
    boundary = (
        run.start_date if run.run_type == "manual"
        else context.get("data_interval_end") or run.start_date
    )
    local = pendulum.instance(boundary).in_timezone("Asia/Seoul")
    if report_type == "weekly":
        target = local.start_of("week").subtract(weeks=1)
    elif report_type == "monthly":
        target = local.start_of("month").subtract(months=1)
    elif report_type == "daily":
        target = local.subtract(days=1)
    else:
        raise ValueError(f"Unknown report type: {report_type}")
    return target.to_date_string()


def submit_report(report_type, **context):
    target = report_date(report_type, context)
    job = _call("POST", "/v1/reports", {"type": report_type, "date": target})
    log.info("AIOps %s date=%s job_id=%s", report_type, target, job["job_id"])
    return job["job_id"]


def submit_daily(**context):
    return submit_report("daily", **context)


def daily_dependency_date(logical_date, report_type, **context):
    """Daily logical date is one day before its 01:00 interval end."""
    import pendulum

    target = pendulum.parse(report_date(report_type, context), tz="Asia/Seoul")
    if report_type == "weekly":
        end = target.start_of("week").add(weeks=1)
    elif report_type == "monthly":
        end = target.start_of("month").add(months=1)
    else:
        raise ValueError(f"Unknown aggregate report type: {report_type}")
    return end.subtract(days=1).replace(hour=1)


def run_until_completed(**context):
    from airflow.exceptions import AirflowFailException

    job_id = context["ti"].xcom_pull(task_ids="submit_report")
    if not job_id:
        raise AirflowFailException("Missing AIOps job_id")
    try:
        return get_client().advance(job_id)
    except (AIOpsAPIError, RuntimeError) as exc:
        raise AirflowFailException(str(exc)) from None

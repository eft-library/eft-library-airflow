"""AIOps HTTP orchestration. Analysis retries remain in the server's DB queue."""

import logging

import requests

log = logging.getLogger(__name__)
TRANSIENT_HTTP = {409, 429, 500, 502, 503, 504}


class AIOpsAPIError(RuntimeError):
    def __init__(self, status_code):
        self.status_code = status_code
        # Do not include request headers or potentially sensitive response bodies.
        super().__init__(f"AIOps API HTTP {status_code}")


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

    def completed(self, job_id):
        job = self.request("GET", f"/v1/jobs/{job_id}")
        state = job["status"]
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
            self.request("POST", "/v1/worker/run-once", worker=True)
            return self.completed(job_id)
        except (requests.ConnectionError, requests.Timeout):
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
    if result.get("status") == "partial":
        # Keep coverage in the server, without dumping collected logs into Airflow.
        log.warning("AIOps collection is partial; consult report coverage")


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

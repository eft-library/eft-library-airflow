import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins"))
from custom_module.aiops_api import AIOpsClient, AIOpsAPIError, AIOpsStreamInterrupted, submit_daily, submit_report, report_date, daily_dependency_date, collect


class AIOpsTests(unittest.TestCase):
    def setUp(self):
        self.client = AIOpsClient("http://example:9023", "test-key")

    def test_report_date_is_stable_for_scheduled_and_manual_runs(self):
        import pendulum

        run = Mock()
        run.conf = {}
        run.run_type = "scheduled"
        run.start_date = pendulum.datetime(2026, 10, 30, tz="Asia/Seoul")
        context = {"dag_run": run, "data_interval_end": pendulum.datetime(2026, 10, 28, 1, tz="Asia/Seoul")}
        with patch("custom_module.aiops_api._call", return_value={"job_id": "target"}) as call:
            self.assertEqual(submit_daily(**context), "target")
            self.assertEqual(call.call_args.args[2]["date"], "2026-10-27")
            run.run_type = "manual"
            submit_daily(**context)
            self.assertEqual(call.call_args.args[2]["date"], "2026-10-29")
            run.conf = {"date": "2026-10-20"}
            submit_daily(**context)
            self.assertEqual(call.call_args.args[2]["date"], "2026-10-20")

    def test_aggregate_periods_and_daily_dependencies(self):
        import pendulum

        for kind, boundary, target, dependency in [
            ("weekly", "2026-11-02T01:00:00+09:00", "2026-10-26", "2026-11-01T01:00:00+09:00"),
            ("monthly", "2026-11-01T01:00:00+09:00", "2026-10-01", "2026-10-31T01:00:00+09:00"),
            ("monthly", "2027-01-01T01:00:00+09:00", "2026-12-01", "2026-12-31T01:00:00+09:00"),
            ("monthly", "2028-03-01T01:00:00+09:00", "2028-02-01", "2028-02-29T01:00:00+09:00"),
        ]:
            with self.subTest(kind=kind, boundary=boundary):
                run = Mock(conf={}, run_type="scheduled")
                run.start_date = pendulum.parse(boundary).add(days=10)
                context = {"dag_run": run, "data_interval_end": pendulum.parse(boundary)}
                self.assertEqual(report_date(kind, context), target)
                self.assertEqual(daily_dependency_date(None, kind, **context), pendulum.parse(dependency))
                with patch("custom_module.aiops_api._call", return_value={"job_id": "target"}) as call:
                    self.assertEqual(submit_report(kind, **context), "target")
                    call.assert_called_once_with("POST", "/v1/reports", {"type": kind, "date": target})

    def test_explicit_aggregate_date_controls_daily_dependency(self):
        import pendulum

        run = Mock(conf={"date": "2026-10-15"}, run_type="manual")
        context = {"dag_run": run}
        self.assertEqual(report_date("weekly", context), "2026-10-15")
        self.assertEqual(daily_dependency_date(None, "weekly", **context), pendulum.datetime(2026, 10, 18, 1, tz="Asia/Seoul"))
        self.assertEqual(daily_dependency_date(None, "monthly", **context), pendulum.datetime(2026, 10, 31, 1, tz="Asia/Seoul"))

    def test_collection_logs_coverage_and_database_registration(self):
        for status in ["completed", "partial"]:
            result = {"status": status, "coverage": {"fastapi": {"status": "collected"}},
                      "database_registration": {"status": "ready"}}
            with patch("custom_module.aiops_api._call", return_value=result) as call, patch("custom_module.aiops_api.log") as logger:
                collect()
                call.assert_called_once_with("POST", "/v1/collect", {})
                self.assertEqual(logger.info.call_count, 3)
                logger.info.assert_any_call("AIOps collection coverage service=%s: %s", "fastapi", result["coverage"]["fastapi"])
                logger.info.assert_any_call("AIOps collection database_registration=%s", result["database_registration"])
                self.assertEqual(logger.warning.call_count, int(status == "partial"))

    def test_investigation_worker_checks_exact_id_and_ignores_idle(self):
        for initial in ["PENDING", "RUNNING"]:
            for final in ["PENDING", "RUNNING", "COMPLETED"]:
                self.client.request = Mock(side_effect=[
                    {"status": initial, "report_id": "daily-v2"},
                    {"status": "idle"}, {"status": final, "report_id": "daily-v2"},
                ])
                self.assertEqual(self.client.advance_investigation("inv"), final == "COMPLETED")
                self.assertEqual(self.client.request.call_args_list[1].args, ("POST", "/v1/investigations/worker/run-once"))
                self.assertEqual(self.client.request.call_args_list[1].kwargs, {"body": {"investigation_id": "inv"}, "worker": True})
                self.assertEqual(self.client.request.call_args.args, ("GET", "/v1/investigations/inv"))

    def test_completed_investigation_reuses_result_without_worker(self):
        self.client.request = Mock(return_value={"status": "COMPLETED"})
        self.assertTrue(self.client.advance_investigation("inv"))
        self.client.request.assert_called_once_with("GET", "/v1/investigations/inv")

    def test_investigation_terminal_errors_fail_without_worker(self):
        for state in ["FAILED", "TIMEOUT", "UNKNOWN"]:
            self.client.request = Mock(return_value={"status": state, "error": "execution"})
            with self.assertRaisesRegex(RuntimeError, "error=execution"):
                self.client.advance_investigation("inv")
            self.assertEqual(self.client.request.call_count, 1)

    def test_investigation_retry_preserves_id_and_rechecks_before_worker(self):
        for error in [requests.Timeout(), requests.ConnectionError(), AIOpsAPIError(409), AIOpsAPIError(503)]:
            self.client.request = Mock(side_effect=[{"status": "PENDING"}, error])
            self.assertFalse(self.client.advance_investigation("inv"))
            self.client.request = Mock(return_value={"status": "COMPLETED"})
            self.assertTrue(self.client.advance_investigation("inv"))
            self.client.request.assert_called_once_with("GET", "/v1/investigations/inv")
        self.client.request = Mock(side_effect=AIOpsAPIError(401))
        with self.assertRaises(AIOpsAPIError):
            self.client.advance_investigation("inv")

    def test_submit_investigation_uses_exact_completed_revision_and_stable_key(self):
        from types import ModuleType
        from custom_module.aiops_api import submit_investigation

        exceptions = ModuleType("airflow.exceptions")
        exceptions.AirflowFailException = RuntimeError
        ti = Mock()
        ti.xcom_pull.return_value = "daily-job"
        with patch.dict(sys.modules, {"airflow.exceptions": exceptions}):
            with patch("custom_module.aiops_api._call", side_effect=[
                {"status": "COMPLETED", "report_id": "daily-v2"},
                {"investigation_id": "inv", "status": "PENDING"},
            ] * 2) as call:
                for _ in range(2):
                    self.assertEqual(submit_investigation(ti=ti), "inv")
                self.assertEqual(call.call_args_list[0].args, ("GET", "/v1/jobs/daily-job"))
                self.assertEqual(call.call_args_list[1].args, ("POST", "/v1/investigations", {"report_id": "daily-v2", "request_key": "default"}))
                self.assertEqual(call.call_args_list[1], call.call_args_list[3])
            for job in [{"status": "PENDING", "report_id": "daily-v2"}, {"status": "COMPLETED"}]:
                with patch("custom_module.aiops_api._call", return_value=job) as call:
                    with self.assertRaises(RuntimeError):
                        submit_investigation(ti=ti)
                    self.assertEqual(call.call_count, 1)

    def test_investigation_worker_uses_long_json_read_timeout(self):
        with patch("custom_module.aiops_api.requests.request") as request:
            request.return_value.ok = True
            self.client.request("POST", "/v1/investigations/worker/run-once", body={"investigation_id": "inv"}, worker=True)
            self.assertEqual(request.call_args.kwargs["timeout"], (10, 900))
            self.assertEqual(request.call_args.kwargs["json"], {"investigation_id": "inv"})

    def test_auth_and_worker_timeout(self):
        with patch("custom_module.aiops_api.requests.request") as request:
            request.return_value.ok = True
            self.client.request("POST", "/v1/worker/run-once", worker=True)
            self.assertEqual(request.call_args.kwargs["headers"], {"X-AIOps-Key": "test-key"})
            self.assertEqual(request.call_args.kwargs["timeout"], (10, 900))

    def stream_response(self, events):
        response = Mock(ok=True, headers={"Content-Type": "text/event-stream; charset=utf-8"})
        response.iter_lines.return_value = iter(events)
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)
        return context, response

    def test_stream_logs_messages_before_receiving_final_event(self):
        events = [
            {"event": "codex.message", "message": "분석 진행 중", "job_id": "target"},
            {"event": "codex.turn.completed", "usage": {"input_tokens": 100}},
            {"event": "heartbeat", "elapsed_seconds": 10},
            {"event": "worker.report", "severity": "low", "summary": "분석 완료"},
            {"event": "worker.finished", "job": {"job_id": "target", "status": "COMPLETED"}, "dropped_events": 2},
        ]
        context, response = self.stream_response([])
        with patch("custom_module.aiops_api.requests.post", return_value=context) as post, patch("custom_module.aiops_api.log") as logger:
            def lines():
                yield ": keepalive"
                yield "event: codex.message"
                yield ""
                for index, event in enumerate(events):
                    if index == 1:
                        self.assertIn("분석", logger.info.call_args.args[-1])
                    yield "data: " + json.dumps(event, ensure_ascii=False)
            response.iter_lines.return_value = lines()
            self.assertEqual(self.client.run_worker_stream()["status"], "COMPLETED")
            self.assertTrue(post.call_args.kwargs["stream"])
            self.assertEqual(post.call_args.kwargs["timeout"], (10, 45))
            self.assertEqual(post.call_args.kwargs["headers"], {"X-AIOps-Key": "test-key"})
            response.iter_lines.assert_called_once_with(chunk_size=1, decode_unicode=True)
            self.assertEqual(response.encoding, "utf-8")
            logger.warning.assert_called_once()
            context.__exit__.assert_called_once()

    def test_truncated_malformed_and_error_streams_recheck_job_later(self):
        for lines in [[], ["data: invalid"], ["data: []"],
                      ['data: {"event":"error","error":"database"}'],
                      ['data: {"event":"worker.finished","job":null}']]:
            context, response = self.stream_response(lines)
            with patch("custom_module.aiops_api.requests.post", return_value=context):
                self.client.request = Mock(return_value={"status": "PENDING"})
                self.assertFalse(self.client.advance("target"))
                self.client.request.assert_called_once_with("GET", "/v1/jobs/target")
                context.__exit__.assert_called_once()

    def test_stream_http_errors_use_existing_retry_policy(self):
        for status, retry in [(409, True), (503, True), (401, False), (404, False)]:
            context, response = self.stream_response([])
            response.ok = False
            response.status_code = status
            self.client.request = Mock(return_value={"status": "PENDING"})
            with patch("custom_module.aiops_api.requests.post", return_value=context):
                if retry:
                    self.assertFalse(self.client.advance("target"))
                else:
                    with self.assertRaises(AIOpsAPIError):
                        self.client.advance("target")

    def test_stream_time_limit_is_enforced_and_connection_closed(self):
        context, response = self.stream_response(['data: {"event":"heartbeat"}'])
        with patch("custom_module.aiops_api.requests.post", return_value=context), patch("custom_module.aiops_api.time.monotonic", side_effect=[0, 901]):
            with self.assertRaises(AIOpsStreamInterrupted):
                self.client.run_worker_stream()
            context.__exit__.assert_called_once()

    def test_completed_does_not_run_worker(self):
        self.client.request = Mock(return_value={"status": "COMPLETED"})
        self.assertTrue(self.client.advance("target"))
        self.client.request.assert_called_once_with("GET", "/v1/jobs/target")

    def test_other_job_completion_is_not_target_success(self):
        self.client.run_worker_stream = Mock(return_value={"status": "COMPLETED", "job_id": "other"})
        self.client.request = Mock(side_effect=[{"status": "PENDING"}, {"status": "PENDING"}])
        self.assertFalse(self.client.advance("target"))
        self.assertEqual(self.client.request.call_args.args, ("GET", "/v1/jobs/target"))

    def test_running_job_can_trigger_server_recovery(self):
        self.client.run_worker_stream = Mock(return_value={"status": "COMPLETED"})
        self.client.request = Mock(side_effect=[{"status": "RUNNING"}, {"status": "COMPLETED"}])
        self.assertTrue(self.client.advance("target"))

    def test_interruption_and_busy_retry_same_job(self):
        for error in [requests.Timeout(), requests.ConnectionError(), AIOpsAPIError(409), AIOpsAPIError(503)]:
            self.client.request = Mock(return_value={"status": "PENDING"})
            self.client.run_worker_stream = Mock(side_effect=error)
            self.assertFalse(self.client.advance("target"))
            self.client.request = Mock(return_value={"status": "COMPLETED"})
            self.assertTrue(self.client.advance("target"))
            self.client.request.assert_called_once_with("GET", "/v1/jobs/target")

    def test_terminal_and_auth_failures_are_not_success(self):
        for state in ["FAILED", "TIMEOUT", "CANCELLED", "UNKNOWN"]:
            self.client.request = Mock(return_value={"status": state})
            with self.assertRaises(RuntimeError):
                self.client.advance("target")
            self.assertEqual(self.client.request.call_count, 1)
        self.client.request = Mock(side_effect=AIOpsAPIError(401))
        with self.assertRaises(AIOpsAPIError):
            self.client.advance("target")


if __name__ == "__main__":
    unittest.main()

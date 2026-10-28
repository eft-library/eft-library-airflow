import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins"))
from custom_module.aiops_api import AIOpsClient, AIOpsAPIError, submit_daily


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

    def test_auth_and_worker_timeout(self):
        with patch("custom_module.aiops_api.requests.request") as request:
            request.return_value.ok = True
            self.client.request("POST", "/v1/worker/run-once", worker=True)
            self.assertEqual(request.call_args.kwargs["headers"], {"X-AIOps-Key": "test-key"})
            self.assertEqual(request.call_args.kwargs["timeout"], (10, 900))

    def test_completed_does_not_run_worker(self):
        self.client.request = Mock(return_value={"status": "COMPLETED"})
        self.assertTrue(self.client.advance("target"))
        self.client.request.assert_called_once_with("GET", "/v1/jobs/target")

    def test_other_job_completion_is_not_target_success(self):
        self.client.request = Mock(side_effect=[
            {"status": "PENDING"}, {"status": "COMPLETED", "job_id": "other"},
            {"status": "PENDING"},
        ])
        self.assertFalse(self.client.advance("target"))
        self.assertEqual(self.client.request.call_args.args, ("GET", "/v1/jobs/target"))

    def test_running_job_can_trigger_server_recovery(self):
        self.client.request = Mock(side_effect=[{"status": "RUNNING"}, {}, {"status": "COMPLETED"}])
        self.assertTrue(self.client.advance("target"))

    def test_interruption_and_busy_retry_same_job(self):
        for error in [requests.Timeout(), requests.ConnectionError(), AIOpsAPIError(409), AIOpsAPIError(503)]:
            self.client.request = Mock(side_effect=[{"status": "PENDING"}, error])
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

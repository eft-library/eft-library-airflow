"""Conditional external dependency for monthly AIOps aggregation."""
from airflow.providers.standard.sensors.external_task import ExternalTaskSensor
from custom_module.aiops_api import weekly_dependency_date


class MonthlyWeeklyReportSensor(ExternalTaskSensor):
    def poke(self, context):
        if weekly_dependency_date(None, **context) is None:
            self.log.info('Month boundary is not Monday; no weekly report dependency')
            return True
        return super().poke(context)

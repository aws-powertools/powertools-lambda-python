from __future__ import annotations

from enum import Enum, auto
from typing import Any, List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CloudWatchAlarmStateValue(Enum):
    OK = auto()
    ALARM = auto()
    INSUFFICIENT_DATA = auto()


class CloudWatchAlarmState(DictWrapper):
    @property
    def value(self) -> CloudWatchAlarmStateValue:
        """
        Overall state of the alarm.
        """
        return CloudWatchAlarmStateValue[self["value"]]

    @property
    def reason(self) -> Optional[str]:
        """
        Reason why alarm was changed to this state.
        """
        return self.get("reason")

    @property
    def reason_data(self) -> Optional[str]:
        """
        Additional data to back up the reason, usually contains the evaluated data points,
        the calculated threshold and timestamps.
        """
        return self.get("reasonData", None)

    @property
    def reason_data_decoded(self) -> Optional[Any]:
        if self.reason_data is None:
            return None

        return self._json_deserializer(self.reason_data)

    @property
    def timestamp(self) -> str:
        """
        Timestamp of this state change in ISO-8601 format.
        """
        return self["timestamp"]


class CloudWatchAlarmMetric(DictWrapper):
    def __init__(self, data: dict):
        super().__init__(data)

        self._metric_stat: dict | None = self.get("metricStat")

    @property
    def metric_id(self) -> str:
        """
        Unique ID of the alarm metric.
        """
        return self["id"]

    @property
    def expression(self) -> Optional[str]:
        """
        The mathematical expression for calculating the metric, if applicable.
        """
        return self.get("expression", None)

    @property
    def label(self) -> Optional[str]:
        """
        Optional label of the metric.
        """
        return self.get("label", None)

    @property
    def namespace(self) -> Optional[str]:
        """
        Namespace of the correspondent CloudWatch Metric.
        """
        if self._metric_stat is not None:
            return self._metric_stat.get("metric", {}).get("namespace", None)

        return None

    @property
    def name(self) -> Optional[str]:
        """
        Name of the correspondent CloudWatch Metric.
        """
        if self._metric_stat is not None:
            return self._metric_stat.get("metric", {}).get("name", None)

        return None

    @property
    def dimensions(self) -> Optional[dict]:
        """
        Additional dimensions of the correspondent CloudWatch Metric, if available.
        """
        if self._metric_stat is not None:
            return self._metric_stat.get("metric", {}).get("dimensions", None)

        return None

    @property
    def period(self) -> Optional[int]:
        """
        Metric evaluation period, in seconds.
        """
        if self._metric_stat is not None:
            return self._metric_stat.get("period", None)

        return None

    @property
    def stat(self) -> Optional[str]:
        """
        Statistical aggregation of metric points, e.g. Average, SampleCount, etc.
        """
        if self._metric_stat is not None:
            return self._metric_stat.get("stat", None)

        return None

    @property
    def return_data(self) -> bool:
        """
        Whether this metric data is used to determine the state of the alarm or not.
        """
        return self["returnData"]


class CloudWatchAlarmEvent(DictWrapper):
    @property
    def source(self) -> str:
        """
        Source of the triggered event, usually it is "aws.cloudwatch".
        """
        return self["source"]

    @property
    def alarm_arn(self) -> str:
        """
        The ARN of the CloudWatch Alarm.
        """
        return self["alarmArn"]

    @property
    def region(self) -> str:
        """
        The AWS region in which the Alarm is active.
        """
        return self["region"]

    @property
    def source_account_id(self) -> str:
        """
        The AWS Account ID that the Alarm is deployed to.
        """
        return self["accountId"]

    @property
    def timestamp(self) -> str:
        """
        Alarm state change event timestamp in ISO-8601 format.
        """
        return self["time"]

    @property
    def alarm_name(self) -> str:
        """
        Alarm name.
        """
        return self["alarmData"]["alarmName"]

    @property
    def alarm_description(self) -> Optional[str]:
        """
        Optional description for the Alarm.
        """
        return self["alarmData"].get("configuration", {}).get("description", None)

    @property
    def state(self):
        """
        The current state of the Alarm.
        """
        return CloudWatchAlarmState(self.get("alarmData").get("state"))

    @property
    def previous_state(self):
        """
        The previous state of the Alarm.
        """
        return CloudWatchAlarmState(self.get("alarmData").get("previousState"))

    @property
    def alarm_metrics(self) -> Optional[List[CloudWatchAlarmMetric]]:
        maybe_metrics = self["alarmData"].get("configuration", {}).get("metrics", None)

        if maybe_metrics is not None:
            return [CloudWatchAlarmMetric(i) for i in maybe_metrics]

        return None

from __future__ import annotations

from functools import cached_property
from typing import Any, Dict, List, Literal, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CloudWatchAlarmState(DictWrapper):
    @property
    def value(self) -> Literal["OK", "ALARM", "INSUFFICIENT_DATA"]:
        """
        Overall state of the alarm.
        """
        return self["value"]

    @property
    def reason(self) -> str:
        """
        Reason why alarm was changed to this state.
        """
        return self["reason"]

    @property
    def reason_data(self) -> str:
        """
        Additional data to back up the reason, usually contains the evaluated data points,
        the calculated threshold and timestamps.
        """
        return self["reasonData"]

    @cached_property
    def reason_data_decoded(self) -> Optional[Any]:
        """
        Deserialized version of reason_data.
        """

        return self._json_deserializer(self.reason_data) if self.reason_data else None

    @property
    def actions_suppressed_by(self) -> Optional[Literal["Alarm", "ExtensionPeriod", "WaitPeriod"]]:
        """
        Describes why the actions when the value is `ALARM` are suppressed in a composite
        alarm.
        """
        return self.get("actionsSuppressedBy", None)

    @property
    def actions_suppressed_reason(self) -> Optional[str]:
        """
        Captures the reason for action suppression.
        """
        return self.get("actionsSuppressedReason", None)

    @property
    def timestamp(self) -> str:
        """
        Timestamp of this state change in ISO-8601 format.
        """
        return self["timestamp"]


class CloudWatchAlarmMetric(DictWrapper):
    @property
    def metric_id(self) -> str:
        """
        Unique ID of the alarm metric.
        """
        return self["id"]

    @property
    def expression(self) -> Optional[str]:
        """
        Optional expression of the alarm metric.
        """
        return self.get("expression", None)

    @property
    def label(self) -> Optional[str]:
        """
        Optional label of the alarm metric.
        """
        return self.get("label", None)

    @property
    def return_data(self) -> bool:
        """
        Whether this metric data is used to determine the state of the alarm or not.
        """
        return self["returnData"]

    @property
    def metric_stat(self) -> CloudWatchAlarmMetricStat:
        return CloudWatchAlarmMetricStat(self["metricStat"])


class CloudWatchAlarmMetricStat(DictWrapper):
    @property
    def period(self) -> Optional[int]:
        """
        Metric evaluation period, in seconds.
        """
        return self.get("period", None)

    @property
    def stat(self) -> Optional[str]:
        """
        Statistical aggregation of metric points, e.g. Average, SampleCount, etc.
        """
        return self.get("stat", None)

    @property
    def unit(self) -> Optional[str]:
        """
        Unit for metric.
        """
        return self.get("unit", None)

    @property
    def metric(self) -> Optional[Dict]:
        """
        Metric details
        """
        return self.get("metric", {})


class CloudWatchAlarmData(DictWrapper):
    @property
    def alarm_name(self) -> str:
        """
        Alarm name.
        """
        return self["alarmName"]

    @property
    def state(self) -> CloudWatchAlarmState:
        """
        The current state of the Alarm.
        """
        return CloudWatchAlarmState(self["state"])

    @property
    def previous_state(self) -> CloudWatchAlarmState:
        """
        The previous state of the Alarm.
        """
        return CloudWatchAlarmState(self["previousState"])

    @property
    def configuration(self) -> CloudWatchAlarmConfiguration:
        """
        The configuration of the Alarm.
        """
        return CloudWatchAlarmConfiguration(self["configuration"])


class CloudWatchAlarmConfiguration(DictWrapper):
    @property
    def description(self) -> Optional[str]:
        """
        Optional description for the Alarm.
        """
        return self.get("description", None)

    @property
    def alarm_rule(self) -> Optional[str]:
        """
        Optional description for the Alarm rule in case of composite alarm.
        """
        return self.get("alarmRule", None)

    @property
    def alarm_actions_suppressor(self) -> Optional[str]:
        """
        Optional action suppression for the Alarm rule in case of composite alarm.
        """
        return self.get("actionsSuppressor", None)

    @property
    def alarm_actions_suppressor_wait_period(self) -> Optional[str]:
        """
        Optional action suppression wait period for the Alarm rule in case of composite alarm.
        """
        return self.get("actionsSuppressorWaitPeriod", None)

    @property
    def alarm_actions_suppressor_extension_period(self) -> Optional[str]:
        """
        Optional action suppression extension period for the Alarm rule in case of composite alarm.
        """
        return self.get("actionsSuppressorExtensionPeriod", None)

    @property
    def metrics(self) -> Optional[List[CloudWatchAlarmMetric]]:
        """
        The metrics evaluated for the Alarm.
        """
        metrics = self.get("metrics")
        return [CloudWatchAlarmMetric(i) for i in metrics] if metrics else None


class CloudWatchAlarmEvent(DictWrapper):
    @property
    def source(self) -> Literal["aws.cloudwatch"]:
        """
        Source of the triggered event.
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
    def alarm_data(self) -> CloudWatchAlarmData:
        """
        Contains basic data about the Alarm and its current and previous states.
        """
        return CloudWatchAlarmData(self["alarmData"])

import json
from enum import Enum, auto
from typing import List, Optional

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
    def reason_data(self) -> Optional[dict]:
        """
        Additional data to back up the reason, usually contains the evaluated data points,
        the calculated threshold and timestamps.
        """
        return json.loads(self.get("reasonData")) if self.get("reasonData") is not None else None

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
    def namespace(self) -> Optional[str]:
        """
        Namespace of the correspondent CloudWatch Metric.
        """
        return self.get("metricStat", {}).get("metric", {}).get("namespace", None)

    @property
    def name(self) -> Optional[str]:
        """
        Name of the correspondent CloudWatch Metric.
        """
        return self.get("metricStat", {}).get("metric", {}).get("name", None)

    @property
    def dimensions(self) -> Optional[dict]:
        """
        Additional dimensions of the correspondent CloudWatch Metric, if available.
        """
        return self.get("metricStat", {}).get("metric", {}).get("dimensions", None)

    @property
    def period(self) -> Optional[int]:
        """
        Metric evaluation period, in seconds.
        """
        return self.get("metricStat", {}).get("period", None)

    @property
    def stat(self) -> Optional[str]:
        """
        Statistical aggregation of metric points, e.g. Average, SampleCount, etc.
        """
        return self.get("metricStat", {}).get("stat", None)

    @property
    def return_data(self) -> bool:
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
        return self.get("alarmData").get("alarmName")

    @property
    def alarm_description(self) -> Optional[str]:
        """
        Optional description for the Alarm.
        """
        return self.get("alarmData").get("configuration", {}).get("description", None)

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
        maybe_metrics = self.get("alarmData", {}).get("configuration", {}).get("metrics", None)

        if maybe_metrics is not None:
            return [CloudWatchAlarmMetric(i) for i in maybe_metrics]

        return None

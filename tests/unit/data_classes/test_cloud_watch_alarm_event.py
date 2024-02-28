import json

from aws_lambda_powertools.utilities.data_classes.cloud_watch_alarm_event import (
    CloudWatchAlarmStateValue,
    CloudWatchAlarmEvent,
)
from tests.functional.utils import load_event


def test_cloud_watch_alarm_event():
    raw_event = load_event("cloudWatchAlarmEvent.json")
    parsed_event = CloudWatchAlarmEvent(raw_event)

    assert parsed_event.source == raw_event["source"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.alarm_arn == raw_event["alarmArn"]
    assert parsed_event.alarm_description == raw_event["alarmData"]["configuration"]["description"]
    assert parsed_event.alarm_name == raw_event["alarmData"]["alarmName"]

    assert parsed_event.state.value == CloudWatchAlarmStateValue[raw_event["alarmData"]["state"]["value"]]
    assert parsed_event.state.reason == raw_event["alarmData"]["state"]["reason"]
    assert parsed_event.state.reason_data == json.loads(raw_event["alarmData"]["state"]["reasonData"])
    assert parsed_event.state.timestamp == raw_event["alarmData"]["state"]["timestamp"]

    assert parsed_event.previous_state.value == CloudWatchAlarmStateValue[raw_event["alarmData"]["previousState"]["value"]]
    assert parsed_event.previous_state.reason == raw_event["alarmData"]["previousState"]["reason"]
    assert parsed_event.previous_state.reason_data == json.loads(raw_event["alarmData"]["previousState"]["reasonData"])
    assert parsed_event.previous_state.timestamp == raw_event["alarmData"]["previousState"]["timestamp"]

    assert parsed_event.alarm_metrics[0].metric_id == raw_event["alarmData"]["configuration"]["metrics"][0]["id"]
    assert (
        parsed_event.alarm_metrics[0].name
        == raw_event["alarmData"]["configuration"]["metrics"][0]["metricStat"]["metric"]["name"]
    )
    assert (
        parsed_event.alarm_metrics[0].namespace
        == raw_event["alarmData"]["configuration"]["metrics"][0]["metricStat"]["metric"]["namespace"]
    )
    assert (
        parsed_event.alarm_metrics[0].dimensions
        == raw_event["alarmData"]["configuration"]["metrics"][0]["metricStat"]["metric"]["dimensions"]
    )
    assert (
        parsed_event.alarm_metrics[0].return_data == raw_event["alarmData"]["configuration"]["metrics"][0]["returnData"]
    )

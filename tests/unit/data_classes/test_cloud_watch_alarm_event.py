import json
from typing import Dict, List

from aws_lambda_powertools.utilities.data_classes import CloudWatchAlarmEvent
from tests.functional.utils import load_event


def test_cloud_watch_alarm_event_single_metric():
    raw_event = load_event("cloudWatchAlarmEventSingleMetric.json")
    parsed_event = CloudWatchAlarmEvent(raw_event)

    assert parsed_event.source == raw_event["source"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.alarm_arn == raw_event["alarmArn"]
    assert parsed_event.alarm_data.alarm_name == raw_event["alarmData"]["alarmName"]

    assert parsed_event.alarm_data.state.value == raw_event["alarmData"]["state"]["value"]
    assert parsed_event.alarm_data.state.reason == raw_event["alarmData"]["state"]["reason"]
    assert parsed_event.alarm_data.state.reason_data == raw_event["alarmData"]["state"]["reasonData"]
    assert parsed_event.alarm_data.state.reason_data_decoded == json.loads(
        raw_event["alarmData"]["state"]["reasonData"],
    )
    assert parsed_event.alarm_data.state.timestamp == raw_event["alarmData"]["state"]["timestamp"]

    assert parsed_event.alarm_data.previous_state.value == raw_event["alarmData"]["previousState"]["value"]
    assert parsed_event.alarm_data.previous_state.reason == raw_event["alarmData"]["previousState"]["reason"]
    assert parsed_event.alarm_data.previous_state.reason_data == raw_event["alarmData"]["previousState"]["reasonData"]
    assert parsed_event.alarm_data.previous_state.reason_data_decoded == json.loads(
        raw_event["alarmData"]["previousState"]["reasonData"],
    )
    assert parsed_event.alarm_data.previous_state.timestamp == raw_event["alarmData"]["previousState"]["timestamp"]

    assert parsed_event.alarm_data.configuration.description == raw_event["alarmData"]["configuration"]["description"]
    assert parsed_event.alarm_data.configuration.alarm_rule is None
    assert parsed_event.alarm_data.configuration.alarm_actions_suppressor is None
    assert parsed_event.alarm_data.configuration.alarm_actions_suppressor_extension_period is None
    assert parsed_event.alarm_data.configuration.alarm_actions_suppressor_wait_period is None

    assert isinstance(parsed_event.alarm_data.configuration.metrics, List)
    # metric position 0
    metric_0 = parsed_event.alarm_data.configuration.metrics[0]
    raw_metric_0 = raw_event["alarmData"]["configuration"]["metrics"][0]
    assert metric_0.metric_id == raw_metric_0["id"]
    assert metric_0.expression == raw_metric_0["expression"]
    assert metric_0.label == raw_metric_0["label"]
    assert metric_0.return_data == raw_metric_0["returnData"]

    # metric position 1
    metric_1 = parsed_event.alarm_data.configuration.metrics[1]
    raw_metric_1 = raw_event["alarmData"]["configuration"]["metrics"][1]
    assert metric_1.metric_id == raw_metric_1["id"]
    assert metric_1.return_data == raw_metric_1["returnData"]
    assert metric_1.metric_stat.stat == raw_metric_1["metricStat"]["stat"]
    assert metric_1.metric_stat.period == raw_metric_1["metricStat"]["period"]
    assert metric_1.metric_stat.unit is None
    assert isinstance(metric_1.metric_stat.metric, Dict)


def test_cloud_watch_alarm_event_composite_metric():
    raw_event = load_event("cloudWatchAlarmEventCompositeMetric.json")
    parsed_event = CloudWatchAlarmEvent(raw_event)

    assert parsed_event.source == raw_event["source"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.alarm_arn == raw_event["alarmArn"]
    assert parsed_event.alarm_data.alarm_name == raw_event["alarmData"]["alarmName"]

    assert parsed_event.alarm_data.state.value == raw_event["alarmData"]["state"]["value"]
    assert parsed_event.alarm_data.state.reason == raw_event["alarmData"]["state"]["reason"]
    assert parsed_event.alarm_data.state.reason_data == raw_event["alarmData"]["state"]["reasonData"]
    assert parsed_event.alarm_data.state.reason_data_decoded == json.loads(
        raw_event["alarmData"]["state"]["reasonData"],
    )
    assert parsed_event.alarm_data.state.timestamp == raw_event["alarmData"]["state"]["timestamp"]

    assert parsed_event.alarm_data.previous_state.value == raw_event["alarmData"]["previousState"]["value"]
    assert parsed_event.alarm_data.previous_state.reason == raw_event["alarmData"]["previousState"]["reason"]
    assert parsed_event.alarm_data.previous_state.reason_data == raw_event["alarmData"]["previousState"]["reasonData"]
    assert parsed_event.alarm_data.previous_state.reason_data_decoded == json.loads(
        raw_event["alarmData"]["previousState"]["reasonData"],
    )
    assert parsed_event.alarm_data.previous_state.timestamp == raw_event["alarmData"]["previousState"]["timestamp"]
    assert (
        parsed_event.alarm_data.previous_state.actions_suppressed_by
        == raw_event["alarmData"]["previousState"]["actionsSuppressedBy"]
    )
    assert (
        parsed_event.alarm_data.previous_state.actions_suppressed_reason
        == raw_event["alarmData"]["previousState"]["actionsSuppressedReason"]
    )

    assert parsed_event.alarm_data.configuration.alarm_rule == raw_event["alarmData"]["configuration"]["alarmRule"]
    assert (
        parsed_event.alarm_data.configuration.alarm_actions_suppressor_wait_period
        == raw_event["alarmData"]["configuration"]["actionsSuppressorWaitPeriod"]
    )
    assert (
        parsed_event.alarm_data.configuration.alarm_actions_suppressor_extension_period
        == raw_event["alarmData"]["configuration"]["actionsSuppressorExtensionPeriod"]
    )
    assert (
        parsed_event.alarm_data.configuration.alarm_actions_suppressor
        == raw_event["alarmData"]["configuration"]["actionsSuppressor"]
    )
    assert isinstance(parsed_event.alarm_data.configuration.metrics, List)

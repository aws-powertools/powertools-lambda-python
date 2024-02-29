from aws_lambda_powertools.utilities.data_classes import CloudWatchAlarmEvent
from tests.functional.utils import load_event


def test_cloud_watch_alarm_event():
    raw_event = load_event("cloudWatchAlarmEvent.json")
    parsed_event = CloudWatchAlarmEvent(raw_event)

    assert parsed_event.source == raw_event["source"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.alarm_arn == raw_event["alarmArn"]
    assert parsed_event.alarm_description == raw_event["alarmData"]["configuration"]["description"]
    assert parsed_event.alarm_name == raw_event["alarmData"]["alarmName"]

    assert parsed_event.state.value == "ALARM"
    assert parsed_event.state.reason == raw_event["alarmData"]["state"]["reason"]
    assert parsed_event.state.reason_data == raw_event["alarmData"]["state"]["reasonData"]
    assert parsed_event.state.reason_data_decoded["queryDate"] == "2024-02-17T11:53:08.423+0000"
    assert parsed_event.state.timestamp == raw_event["alarmData"]["state"]["timestamp"]

    assert parsed_event.previous_state.value == "OK"
    assert parsed_event.previous_state.reason == raw_event["alarmData"]["previousState"]["reason"]
    assert parsed_event.previous_state.reason_data == raw_event["alarmData"]["previousState"]["reasonData"]
    assert parsed_event.previous_state.reason_data_decoded["queryDate"] == "2024-02-17T11:51:31.460+0000"
    assert parsed_event.previous_state.timestamp == raw_event["alarmData"]["previousState"]["timestamp"]

    # test the 'expression' metric
    assert parsed_event.alarm_metrics[0].metric_id == raw_event["alarmData"]["configuration"]["metrics"][0]["id"]
    assert (
        parsed_event.alarm_metrics[0].expression == raw_event["alarmData"]["configuration"]["metrics"][0]["expression"]
    )
    assert parsed_event.alarm_metrics[0].label == raw_event["alarmData"]["configuration"]["metrics"][0]["label"]
    assert (
        parsed_event.alarm_metrics[0].return_data == raw_event["alarmData"]["configuration"]["metrics"][0]["returnData"]
    )

    # test the 'metric' metric
    assert parsed_event.alarm_metrics[1].metric_id == raw_event["alarmData"]["configuration"]["metrics"][1]["id"]
    assert (
        parsed_event.alarm_metrics[1].name
        == raw_event["alarmData"]["configuration"]["metrics"][1]["metricStat"]["metric"]["name"]
    )
    assert (
        parsed_event.alarm_metrics[1].namespace
        == raw_event["alarmData"]["configuration"]["metrics"][1]["metricStat"]["metric"]["namespace"]
    )
    assert (
        parsed_event.alarm_metrics[1].dimensions
        == raw_event["alarmData"]["configuration"]["metrics"][1]["metricStat"]["metric"]["dimensions"]
    )
    assert (
        parsed_event.alarm_metrics[1].return_data == raw_event["alarmData"]["configuration"]["metrics"][1]["returnData"]
    )

from aws_lambda_powertools.utilities.data_classes import CloudWatchLogsEvent
from tests.functional.utils import load_event


def test_cloud_watch_trigger_event():
    raw_event = load_event("cloudWatchLogEvent.json")
    parsed_event = CloudWatchLogsEvent(raw_event)

    decompressed_logs_data = parsed_event.decompress_logs_data
    assert parsed_event.decompress_logs_data == decompressed_logs_data

    json_logs_data = parsed_event.parse_logs_data()
    assert parsed_event.parse_logs_data().raw_event == json_logs_data.raw_event
    log_events = json_logs_data.log_events
    log_event = log_events[0]

    assert json_logs_data.owner == "123456789123"
    assert json_logs_data.log_group == "testLogGroup"
    assert json_logs_data.log_stream == "testLogStream"
    assert json_logs_data.subscription_filters == ["testFilter"]
    assert json_logs_data.message_type == "DATA_MESSAGE"

    assert log_event.get_id == "eventId1"
    assert log_event.timestamp == 1440442987000
    assert log_event.message == "[ERROR] First test message"
    assert log_event.extracted_fields is None

    event2 = CloudWatchLogsEvent(load_event("cloudWatchLogEvent.json"))
    assert parsed_event.raw_event == event2.raw_event

from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from tests.functional.utils import load_event


def test_event_bridge_event():
    raw_event = load_event("eventBridgeEvent.json")
    parsed_event = EventBridgeEvent(raw_event)

    assert parsed_event.get_id == raw_event["id"]
    assert parsed_event.version == raw_event["version"]
    assert parsed_event.account == raw_event["account"]
    assert parsed_event.time == raw_event["time"]
    assert parsed_event.region == raw_event["region"]
    assert parsed_event.resources == raw_event["resources"]
    assert parsed_event.source == raw_event["source"]
    assert parsed_event.detail_type == raw_event["detail-type"]
    assert parsed_event.detail == raw_event["detail"]
    assert parsed_event.replay_name == "replay_archive"

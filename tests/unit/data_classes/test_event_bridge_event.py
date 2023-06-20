from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from tests.functional.utils import load_event


def test_event_bridge_event():
    event = EventBridgeEvent(load_event("eventBridgeEvent.json"))

    assert event.get_id == event["id"]
    assert event.version == event["version"]
    assert event.account == event["account"]
    assert event.time == event["time"]
    assert event.region == event["region"]
    assert event.resources == event["resources"]
    assert event.source == event["source"]
    assert event.detail_type == event["detail-type"]
    assert event.detail == event["detail"]
    assert event.replay_name == "replay_archive"

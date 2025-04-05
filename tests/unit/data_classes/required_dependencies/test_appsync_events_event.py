from aws_lambda_powertools.utilities.data_classes import AppSyncResolverEventsEvent
from tests.functional.utils import load_event


def test_appsync_resolver_event():
    raw_event = load_event("appSyncEventsEvent.json")
    parsed_event = AppSyncResolverEventsEvent(raw_event)

    assert parsed_event.events == raw_event["events"]
    assert parsed_event.out_errors == raw_event["outErrors"]
    assert parsed_event.domain_name == raw_event["request"]["domainName"]
    assert parsed_event.info.channel == raw_event["info"]["channel"]
    assert parsed_event.info.channel_path == raw_event["info"]["channel"]["path"]
    assert parsed_event.info.channel_segments == raw_event["info"]["channel"]["segments"]
    assert parsed_event.info.channel_namespace == raw_event["info"]["channelNamespace"]
    assert parsed_event.info.operation == raw_event["info"]["operation"]

from datetime import datetime

from aws_lambda_powertools.utilities.data_classes.iot_registry_event import (
    IoTCoreAddOrDeleteFromThingGroupEvent,
    IoTCoreAddOrRemoveFromThingGroupEvent,
    IoTCoreThingEvent,
    IoTCoreThingGroupEvent,
    IoTCoreThingTypeAssociationEvent,
    IoTCoreThingTypeEvent,
)
from tests.functional.utils import load_event


def test_iotcore_thing_event():
    raw_event = load_event("iotRegistryEventsThingEvent.json")
    parsed_event = IoTCoreThingEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_name == raw_event["thingName"]
    assert parsed_event.version_number == raw_event["versionNumber"]
    assert parsed_event.thing_type_name == raw_event.get("thingTypeName")
    assert parsed_event.attributes == raw_event["attributes"]
    assert parsed_event.event_id == raw_event["eventId"]

    # Validate timestamp conversion
    # Original field is int
    expected_timestamp = datetime.fromtimestamp(
        raw_event["timestamp"] / 1000 if raw_event["timestamp"] > 10**10 else raw_event["timestamp"],
    )
    assert parsed_event.timestamp == expected_timestamp


def test_iotcore_thing_type_event():
    raw_event = load_event("iotRegistryEventsThingTypeEvent.json")
    parsed_event = IoTCoreThingTypeEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_type_name == raw_event["thingTypeName"]
    assert parsed_event.is_deprecated == raw_event["isDeprecated"]
    assert parsed_event.deprecation_date == raw_event["deprecationDate"]
    assert parsed_event.searchable_attributes == raw_event["searchableAttributes"]
    assert parsed_event.propagating_attributes == raw_event["propagatingAttributes"]
    assert parsed_event.description == raw_event["description"]
    assert parsed_event.thing_type_id == raw_event["thingTypeId"]


def test_iotcore_thing_type_association_event():
    raw_event = load_event("iotRegistryEventsThingTypeAssociationEvent.json")
    parsed_event = IoTCoreThingTypeAssociationEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.thing_type_name == raw_event["thingTypeName"]
    assert parsed_event.thing_name == raw_event["thingName"]


def test_iotcore_thing_group_event():
    raw_event = load_event("iotRegistryEventsThingGroupEvent.json")
    parsed_event = IoTCoreThingGroupEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_group_name == raw_event["thingGroupName"]
    assert parsed_event.thing_group_id == raw_event["thingGroupId"]
    assert parsed_event.version_number == raw_event["versionNumber"]
    assert parsed_event.parent_group_name == raw_event["parentGroupName"]
    assert parsed_event.parent_group_id == raw_event["parentGroupId"]
    assert parsed_event.description == raw_event["description"]
    assert parsed_event.root_to_parent_thing_groups == raw_event["rootToParentThingGroups"]
    assert parsed_event.attributes == raw_event["attributes"]
    assert parsed_event.dynamic_group_mapping_id == raw_event["dynamicGroupMappingId"]


def test_iotcore_add_or_remove_from_thing_group_event():
    raw_event = load_event("iotRegistryEventsAddOrRemoveFromThingGroupEvent.json")
    parsed_event = IoTCoreAddOrRemoveFromThingGroupEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.group_id == raw_event["groupId"]
    assert parsed_event.group_arn == raw_event["groupArn"]
    assert parsed_event.thing_arn == raw_event["thingArn"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.membership_id == raw_event["membershipId"]


def test_iotcore_add_or_delete_from_thing_group_event():
    raw_event = load_event("iotRegistryEventsAddOrDeleteFromThingGroupEvent.json")
    parsed_event = IoTCoreAddOrDeleteFromThingGroupEvent(raw_event)

    assert parsed_event.event_type == raw_event["eventType"]
    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_group_id == raw_event["thingGroupId"]
    assert parsed_event.thing_group_name == raw_event["thingGroupName"]
    assert parsed_event.child_group_id == raw_event["childGroupId"]
    assert parsed_event.child_group_name == raw_event["childGroupName"]
    assert parsed_event.operation == raw_event["operation"]

    expected_timestamp = datetime.fromtimestamp(
        raw_event["timestamp"] / 1000 if raw_event["timestamp"] > 10**10 else raw_event["timestamp"],
    )
    assert parsed_event.timestamp == expected_timestamp

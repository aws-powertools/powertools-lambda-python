from aws_lambda_powertools.utilities.parser.models.iot_registry_events import (
    IoTCoreAddOrDeleteFromThingGroupEvent,
    IoTCoreAddOrRemoveFromThingGroupEvent,
    IoTCoreThingEvent,
    IoTCoreThingGroupEvent,
    IoTCoreThingTypeAssociationEvent,
    IoTCoreThingTypeEvent,
)
from tests.functional.utils import load_event


def test_iot_core_thing_event():
    raw_event = load_event("iotRegistryEventsThingEvent.json")
    parsed_event: IoTCoreThingEvent = IoTCoreThingEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.thing_name == raw_event["thingName"]
    assert parsed_event.version_number == raw_event["versionNumber"]
    assert parsed_event.thing_type_name == raw_event["thingTypeName"]
    assert parsed_event.attributes == raw_event["attributes"]


def test_iot_core_thing_type_event():
    raw_event = load_event("iotRegistryEventsThingTypeEvent.json")
    parsed_event: IoTCoreThingTypeEvent = IoTCoreThingTypeEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_type_id == raw_event["thingTypeId"]
    assert parsed_event.thing_type_name == raw_event["thingTypeName"]
    assert parsed_event.is_deprecated == raw_event["isDeprecated"]
    assert parsed_event.deprecation_date == raw_event["deprecationDate"]
    assert parsed_event.searchable_attributes == raw_event["searchableAttributes"]
    assert parsed_event.propagating_attributes == raw_event["propagatingAttributes"]
    assert parsed_event.description == raw_event["description"]


def test_iot_core_thing_type_association_event():
    raw_event = load_event("iotRegistryEventsThingTypeAssociationEvent.json")
    parsed_event: IoTCoreThingTypeAssociationEvent = IoTCoreThingTypeAssociationEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.thing_name == raw_event["thingName"]
    assert parsed_event.thing_type_name == raw_event["thingTypeName"]


def test_iot_core_thing_group_event():

    raw_event = load_event("iotRegistryEventsThingGroupEvent.json")
    parsed_event: IoTCoreThingGroupEvent = IoTCoreThingGroupEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_group_name == raw_event["thingGroupName"]
    assert parsed_event.version_number == raw_event["versionNumber"]
    assert parsed_event.parent_group_name == raw_event["parentGroupName"]
    assert parsed_event.parent_group_id == raw_event["parentGroupId"]
    assert parsed_event.description == raw_event["description"]
    assert parsed_event.root_to_parent_thing_groups == raw_event["rootToParentThingGroups"]
    assert parsed_event.attributes == raw_event["attributes"]
    assert parsed_event.dynamic_group_mapping_id == raw_event["dynamicGroupMappingId"]


def test_iot_core_add_or_remove_from_thing_group_event():

    raw_event = load_event("iotRegistryEventsAddOrRemoveFromThingGroupEvent.json")
    parsed_event: IoTCoreAddOrRemoveFromThingGroupEvent = IoTCoreAddOrRemoveFromThingGroupEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.group_arn == raw_event["groupArn"]
    assert parsed_event.group_id == raw_event["groupId"]
    assert parsed_event.thing_arn == raw_event["thingArn"]
    assert parsed_event.thing_id == raw_event["thingId"]
    assert parsed_event.membership_id == raw_event["membershipId"]


def test_iot_core_add_or_delete_from_thing_group_event():

    raw_event = load_event("iotRegistryEventsAddOrDeleteFromThingGroupEvent.json")
    parsed_event: IoTCoreAddOrDeleteFromThingGroupEvent = IoTCoreAddOrDeleteFromThingGroupEvent(**raw_event)

    assert parsed_event.event_id == raw_event["eventId"]
    assert parsed_event.event_type == raw_event["eventType"]
    convert_time = int(round(parsed_event.timestamp.timestamp() * 1000))
    assert convert_time == raw_event["timestamp"]
    assert parsed_event.operation == raw_event["operation"]
    assert parsed_event.account_id == raw_event["accountId"]
    assert parsed_event.thing_group_id == raw_event["thingGroupId"]
    assert parsed_event.thing_group_name == raw_event["thingGroupName"]
    assert parsed_event.child_group_id == raw_event["childGroupId"]
    assert parsed_event.child_group_name == raw_event["childGroupName"]

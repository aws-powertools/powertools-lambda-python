from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.parser.models.iot_registry_events import (
    IoTCoreAddOrDeleteFromThingGroupEvent,
    IoTCoreAddOrRemoveFromThingGroupEvent,
    IoTCoreThingEvent,
    IoTCoreThingGroupEvent,
    IoTCoreThingTypeAssociationEvent,
    IoTCoreThingTypeEvent,
)


def test_IoTCoreThingEvent_should_serialize_from_event_data():
    event = {
        "eventType": "THING_EVENT",
        "eventId": "f5ae9b94-8b8e-4d8e-8c8f-b3266dd89853",
        "timestamp": 1234567890123,
        "operation": "CREATED",
        "accountId": "123456789012",
        "thingId": "b604f69c-aa9a-4d4a-829e-c480e958a0b5",
        "thingName": "MyThing",
        "versionNumber": 1,
        "thingTypeName": None,
        "attributes": {"attribute3": "value3", "attribute1": "value1", "attribute2": "value2"},
    }
    parsed_event = parse(event, IoTCoreThingEvent)
    assert parsed_event is not None


def test_IoTCoreThingTypeEvent_should_serialize_from_event_data():
    event = {
        "eventType": "THING_TYPE_EVENT",
        "eventId": "8827376c-4b05-49a3-9b3b-733729df7ed5",
        "timestamp": 1234567890123,
        "operation": "CREATED",
        "accountId": "123456789012",
        "thingTypeId": "c530ae83-32aa-4592-94d3-da29879d1aac",
        "thingTypeName": "MyThingType",
        "isDeprecated": False,
        "deprecationDate": None,
        "searchableAttributes": ["attribute1", "attribute2", "attribute3"],
        "propagatingAttributes": [
            {"userPropertyKey": "key", "thingAttribute": "model"},
            {"userPropertyKey": "key", "connectionAttribute": "iot:ClientId"},
        ],
        "description": "My thing type",
    }
    result = parse(event, IoTCoreThingTypeEvent)
    assert result is not None


def test_IoTCoreThingTypeAssociationEvent_should_serialize_from_event_data():
    event = {
        "eventId": "87f8e095-531c-47b3-aab5-5171364d138d",
        "eventType": "THING_TYPE_ASSOCIATION_EVENT",
        "operation": "ADDED",
        "thingId": "b604f69c-aa9a-4d4a-829e-c480e958a0b5",
        "thingName": "myThing",
        "thingTypeName": "MyThingType",
        "timestamp": 1234567890123,
    }
    result = parse(event, IoTCoreThingTypeAssociationEvent)
    assert result is not None


def test_IoTCoreThingGroupEvent_should_serialize_from_event_data():
    event = {
        "eventType": "THING_GROUP_EVENT",
        "eventId": "8b9ea8626aeaa1e42100f3f32b975899",
        "timestamp": 1603995417409,
        "operation": "UPDATED",
        "accountId": "571EXAMPLE833",
        "thingGroupId": "8757eec8-bb37-4cca-a6fa-403b003d139f",
        "thingGroupName": "Tg_level5",
        "versionNumber": 3,
        "parentGroupName": "Tg_level4",
        "parentGroupId": "5fce366a-7875-4c0e-870b-79d8d1dce119",
        "description": "New description for Tg_level5",
        "rootToParentThingGroups": [
            {
                "groupArn": "arn:aws:iot:us-west-2:571EXAMPLE833:thinggroup/TgTopLevel",
                "groupId": "36aa0482-f80d-4e13-9bff-1c0a75c055f6",
            },
            {
                "groupArn": "arn:aws:iot:us-west-2:571EXAMPLE833:thinggroup/Tg_level1",
                "groupId": "bc1643e1-5a85-4eac-b45a-92509cbe2a77",
            },
            {
                "groupArn": "arn:aws:iot:us-west-2:571EXAMPLE833:thinggroup/Tg_level2",
                "groupId": "0476f3d2-9beb-48bb-ae2c-ea8bd6458158",
            },
            {
                "groupArn": "arn:aws:iot:us-west-2:571EXAMPLE833:thinggroup/Tg_level3",
                "groupId": "1d9d4ffe-a6b0-48d6-9de6-2e54d1eae78f",
            },
            {
                "groupArn": "arn:aws:iot:us-west-2:571EXAMPLE833:thinggroup/Tg_level4",
                "groupId": "5fce366a-7875-4c0e-870b-79d8d1dce119",
            },
        ],
        "attributes": {"attribute1": "value1", "attribute3": "value3", "attribute2": "value2"},
        "dynamicGroupMappingId": None,
    }
    result = parse(event, IoTCoreThingGroupEvent)
    assert result is not None


def test_IoTCoreAddOrRemoveFromThingGroupEvent_should_serialize_from_event_data():
    event = {
        "eventType": "THING_GROUP_MEMBERSHIP_EVENT",
        "eventId": "d684bd5f-6f6e-48e1-950c-766ac7f02fd1",
        "timestamp": 1234567890123,
        "operation": "ADDED",
        "accountId": "123456789012",
        "groupArn": "arn:aws:iot:ap-northeast-2:123456789012:thinggroup/MyChildThingGroup",
        "groupId": "06838589-373f-4312-b1f2-53f2192291c4",
        "thingArn": "arn:aws:iot:ap-northeast-2:123456789012:thing/MyThing",
        "thingId": "b604f69c-aa9a-4d4a-829e-c480e958a0b5",
        "membershipId": "8505ebf8-4d32-4286-80e9-c23a4a16bbd8",
    }
    result = parse(event, IoTCoreAddOrRemoveFromThingGroupEvent)
    assert result is not None


def test_IoTCoreAddOrDeleteFromThingGroupEvent_should_serialize_from_event_data():
    event = {
        "eventType": "THING_GROUP_HIERARCHY_EVENT",
        "eventId": "264192c7-b573-46ef-ab7b-489fcd47da41",
        "timestamp": 1234567890123,
        "operation": "ADDED",
        "accountId": "123456789012",
        "thingGroupId": "8f82a106-6b1d-4331-8984-a84db5f6f8cb",
        "thingGroupName": "MyRootThingGroup",
        "childGroupId": "06838589-373f-4312-b1f2-53f2192291c4",
        "childGroupName": "MyChildThingGroup",
    }
    result = parse(event, IoTCoreAddOrDeleteFromThingGroupEvent)
    assert result is not None

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

EVENT_CRUD_OPERATION = Literal["CREATED", "UPDATED", "DELETED"]
EVENT_ADD_REMOVE_OPERATION = Literal["ADDED", "REMOVED"]


class IoTCoreRegistryEventsBase(DictWrapper):
    @property
    def event_id(self) -> str:
        return self["eventId"]

    @property
    def timestamp(self) -> datetime:
        """
        A Unix timestamp can be in seconds or milliseconds. If the value is 10 digits long, it's in seconds.
        If it's 13 digits long, it's in milliseconds and should be divided by 1000 to convert it to seconds.
        """
        ts = self["timestamp"]
        return datetime.fromtimestamp(ts / 1000 if ts > 10**10 else ts)


class IoTCoreThingEvent(IoTCoreRegistryEventsBase):
    """
    Thing Created/Updated/Deleted

    The registry publishes event messages when things are created, updated, or deleted.
    """

    @property
    def event_type(self) -> Literal["THING_EVENT"]:
        return self["eventType"]

    @property
    def operation(self) -> str:
        return self["operation"]

    @property
    def thing_id(self) -> str:
        return self["thingId"]

    @property
    def account_id(self) -> str:
        return self["accountId"]

    @property
    def thing_name(self) -> str:
        return self["thingName"]

    @property
    def version_number(self) -> int:
        return self["versionNumber"]

    @property
    def thing_type_name(self) -> Optional[str]:
        return self.get("thingTypeName")

    @property
    def attributes(self) -> Dict[str, Any]:
        return self["attributes"]


class IoTCoreThingTypeEvent(IoTCoreRegistryEventsBase):
    """
    Thing Type Created/Updated/Deprecated/Undeprecated/Deleted
    The registry publishes event messages when thing types are created, updated, deprecated, undeprecated, or deleted.

    Format:
        $aws/events/thingType/thingTypeName/created
        $aws/events/thingType/thingTypeName/updated
        $aws/events/thingType/thingTypeName/deleted
    """

    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def operation(self) -> EVENT_CRUD_OPERATION:
        return self["operation"]

    @property
    def account_id(self) -> str:
        return self["accountId"]

    @property
    def thing_type_id(self) -> str:
        return self["thingTypeId"]

    @property
    def thing_type_name(self) -> str:
        return self["thingTypeName"]

    @property
    def is_deprecated(self) -> bool:
        return self["isDeprecated"]

    @property
    def deprecation_date(self) -> Optional[datetime]:
        return datetime.fromisoformat(self["deprecationDate"]) if self.get("deprecationDate") else None

    @property
    def searchable_attributes(self) -> List[str]:
        return self["searchableAttributes"]

    @property
    def propagating_attributes(self) -> List[Dict[str, str]]:
        return self["propagatingAttributes"]

    @property
    def description(self) -> str:
        return self["description"]


class IoTCoreThingTypeAssociationEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes event messages when a thing type is associated or disassociated with a thing.

    Format:
        $aws/events/thingTypeAssociation/thing/thingName/thingType/typeName/added
        $aws/events/thingTypeAssociation/thing/thingName/thingType/typeName/removed
    """

    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def operation(self) -> Literal["THING_TYPE_ASSOCIATION_EVENT"]:
        return self["operation"]

    @property
    def thing_id(self) -> str:
        return self["thingId"]

    @property
    def thing_name(self) -> str:
        return self["thingName"]

    @property
    def thing_type_name(self) -> str:
        return self["thingTypeName"]


class IoTCoreThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes the following event messages when a thing group is created, updated, or deleted.

    Format:
        $aws/events/thingGroup/groupName/created
        $aws/events/thingGroup/groupName/updated
        $aws/events/thingGroup/groupName/deleted
    """

    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def operation(self) -> EVENT_CRUD_OPERATION:
        return self["operation"]

    @property
    def account_id(self) -> str:
        return self["accountId"]

    @property
    def thing_group_id(self) -> str:
        return self["thingGroupId"]

    @property
    def thing_group_name(self) -> str:
        return self["thingGroupName"]

    @property
    def version_number(self) -> int:
        return self["versionNumber"]

    @property
    def parent_group_name(self) -> Optional[str]:
        return self.get("parentGroupName")

    @property
    def parent_group_id(self) -> Optional[str]:
        return self.get("parentGroupId")

    @property
    def description(self) -> str:
        return self["description"]

    @property
    def root_to_parent_thing_groups(self) -> List[Dict[str, str]]:
        return self["rootToParentThingGroups"]

    @property
    def attributes(self) -> Dict[str, Any]:
        return self["attributes"]

    @property
    def dynamic_group_mapping_id(self) -> Optional[str]:
        return self.get("dynamicGroupMappingId")


class IoTCoreAddOrRemoveFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes event messages when a thing is added to or removed from a thing group.

    Format:
        $aws/events/thingGroupMembership/thingGroup/thingGroupName/thing/thingName/added
        $aws/events/thingGroupMembership/thingGroup/thingGroupName/thing/thingName/removed
    """

    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def operation(self) -> EVENT_ADD_REMOVE_OPERATION:
        return self["operation"]

    @property
    def account_id(self) -> str:
        return self["accountId"]

    @property
    def group_arn(self) -> str:
        return self["groupArn"]

    @property
    def group_id(self) -> str:
        return self["groupId"]

    @property
    def thing_arn(self) -> str:
        return self["thingArn"]

    @property
    def thing_id(self) -> str:
        return self["thingId"]

    @property
    def membership_id(self) -> str:
        return self["membershipId"]


class IoTCoreAddOrDeleteFromThingGroupEvent(IoTCoreRegistryEventsBase):
    @property
    def event_type(self) -> str:
        return self["eventType"]

    @property
    def operation(self) -> EVENT_ADD_REMOVE_OPERATION:
        return self["operation"]

    @property
    def account_id(self) -> str:
        return self["accountId"]

    @property
    def thing_group_id(self) -> str:
        return self["thingGroupId"]

    @property
    def thing_group_name(self) -> str:
        return self["thingGroupName"]

    @property
    def child_group_id(self) -> str:
        return self["childGroupId"]

    @property
    def child_group_name(self) -> str:
        return self["childGroupName"]

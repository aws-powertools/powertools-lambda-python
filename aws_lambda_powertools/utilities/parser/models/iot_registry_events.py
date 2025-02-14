from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

EVENT_CRUD_OPERATION = Literal["CREATED", "UPDATED", "DELETED"]
EVENT_ADD_REMOVE_OPERATION = Literal["ADDED", "REMOVED"]


class IoTCoreRegistryEventsBase(BaseModel):
    event_id: str = Field(..., alias="eventId")
    timestamp: datetime


class IoTCoreThingEvent(IoTCoreRegistryEventsBase):
    """
    Thing Created/Updated/Deleted

    The registry publishes event messages when things are created, updated, or deleted.
    """

    event_type: Literal["THING_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_CRUD_OPERATION
    thing_id: str = Field(..., alias="thingId")
    account_id: str = Field(..., alias="accountId")
    thing_name: str = Field(..., alias="thingName")
    version_number: int = Field(..., alias="versionNumber")
    thing_type_name: Optional[str] = Field(None, alias="thingTypeName")
    attributes: Dict[str, Any]


class IoTCoreThingTypeEvent(IoTCoreRegistryEventsBase):
    """
    Thing Type Created/Updated/Deprecated/Undeprecated/Deleted
    The registry publishes event messages when thing types are created, updated, deprecated, undeprecated, or deleted.

    Format:
        $aws/events/thingType/thingTypeName/created
        $aws/events/thingType/thingTypeName/updated
        $aws/events/thingType/thingTypeName/deleted
    """

    event_type: Literal["THING_TYPE_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_CRUD_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_type_id: str = Field(..., alias="thingTypeId")
    thing_type_name: str = Field(..., alias="thingTypeName")
    is_deprecated: bool = Field(..., alias="isDeprecated")
    deprecation_date: Optional[datetime] = Field(None, alias="deprecationDate")
    searchable_attributes: List[str] = Field(..., alias="searchableAttributes")
    propagating_attributes: List[Dict[str, str]] = Field(..., alias="propagatingAttributes")
    description: str


class IoTCoreThingTypeAssociationEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes event messages when a thing type is associated or disassociated with a thing.

    Format:
        $aws/events/thingTypeAssociation/thing/thingName/thingType/typeName/added
        $aws/events/thingTypeAssociation/thing/thingName/thingType/typeName/removed
    """

    event_type: Literal["THING_TYPE_ASSOCIATION_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_ADD_REMOVE_OPERATION
    thing_id: str = Field(..., alias="thingId")
    thing_name: str = Field(..., alias="thingName")
    thing_type_name: str = Field(..., alias="thingTypeName")


class IoTCoreThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes the following event messages when a thing group is created, updated, or deleted.

    Format:
        $aws/events/thingGroup/groupName/created
        $aws/events/thingGroup/groupName/updated
        $aws/events/thingGroup/groupName/deleted
    """

    event_type: Literal["THING_GROUP_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_CRUD_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_group_id: str = Field(..., alias="thingGroupId")
    thing_group_name: str = Field(..., alias="thingGroupName")
    version_number: int = Field(..., alias="versionNumber")
    parent_group_name: Optional[str] = Field(None, alias="parentGroupName")
    parent_group_id: Optional[str] = Field(None, alias="parentGroupId")
    description: str
    root_to_parent_thing_groups: List[Dict[str, str]] = Field(..., alias="rootToParentThingGroups")
    attributes: Dict[str, Any]
    dynamic_group_mapping_id: Optional[str] = Field(None, alias="dynamicGroupMappingId")


class IoTCoreAddOrRemoveFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes event messages when a thing is added to or removed from a thing group.

    Format:
        $aws/events/thingGroupMembership/thingGroup/thingGroupName/thing/thingName/added
        $aws/events/thingGroupMembership/thingGroup/thingGroupName/thing/thingName/removed
    """

    event_type: Literal["THING_GROUP_MEMBERSHIP_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_ADD_REMOVE_OPERATION
    account_id: str = Field(..., alias="accountId")
    group_arn: str = Field(..., alias="groupArn")
    group_id: str = Field(..., alias="groupId")
    thing_arn: str = Field(..., alias="thingArn")
    thing_id: str = Field(..., alias="thingId")
    membership_id: str = Field(..., alias="membershipId")


class IoTCoreAddOrDeleteFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    The registry publishes event messages when a thing group is added to or removed from another thing group.

    Format:
        $aws/events/thingGroupHierarchy/thingGroup/parentThingGroupName/childThingGroup/childThingGroupName/added
        $aws/events/thingGroupHierarchy/thingGroup/parentThingGroupName/childThingGroup/childThingGroupName/removed
    """

    event_type: Literal["THING_GROUP_HIERARCHY_EVENT"] = Field(..., alias="eventType")
    operation: EVENT_ADD_REMOVE_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_group_id: str = Field(..., alias="thingGroupId")
    thing_group_name: str = Field(..., alias="thingGroupName")
    child_group_id: str = Field(..., alias="childGroupId")
    child_group_name: str = Field(..., alias="childGroupName")

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class IoTCoreRegistryEventsBase(BaseModel):
    eventType: str
    eventId: str
    timestamp: int


EVENT_CRUD_OPERATION = Literal["CREATED", "UPDATED", "DELETED"]
EVENT_ADD_REMOVE_OPERATION = Literal["ADDED", "REMOVED"]


class IoTCoreThingEvent(IoTCoreRegistryEventsBase):
    """The 'Thing: created, updated, deleted' event"""

    operation: EVENT_CRUD_OPERATION
    thing_id: str = Field(..., alias="thingId")
    account_id: str = Field(..., alias="accountId")
    thing_name: str = Field(..., alias="thingName")
    version_number: int = Field(..., alias="versionNumber")
    thing_type_name: Optional[str] = Field(None, alias="thingTypeName")
    attributes: Dict[str, Any]


class IoTCoreThingTypeEvent(IoTCoreRegistryEventsBase):
    operation: EVENT_CRUD_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_type_id: str = Field(..., alias="thingTypeId")
    thing_type_name: str = Field(..., alias="thingTypeName")
    is_deprecated: bool = Field(..., alias="isDeprecated")
    deprecation_date: Optional[str] = Field(None, alias="deprecationDate")
    searchable_attributes: List[str] = Field(..., alias="searchableAttributes")
    propagating_attributes: List[Dict[str, str]] = Field(..., alias="propagatingAttributes")
    description: str


class IoTCoreThingTypeAssociationEvent(IoTCoreRegistryEventsBase):
    """Thing Type Associated or Disassociated with a Thing"""

    operation: EVENT_ADD_REMOVE_OPERATION
    thing_id: str = Field(..., alias="thingId")
    thing_name: str = Field(..., alias="thingName")
    thing_type_name: str = Field(..., alias="thingTypeName")


class RootToParentThingGroup(BaseModel):
    group_arn: str = Field(..., alias="groupArn")
    group_id: str = Field(..., alias="groupId")


class IoTCoreThingGroupEvent(IoTCoreRegistryEventsBase):
    """Thing Group Created/Updated/Deleted"""

    operation: EVENT_CRUD_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_group_id: str = Field(..., alias="thingGroupId")
    thing_group_name: str = Field(..., alias="thingGroupName")
    version_number: int = Field(..., alias="versionNumber")
    parent_group_name: Optional[str] = Field(None, alias="parentGroupName")
    parent_group_id: Optional[str] = Field(None, alias="parentGroupId")
    description: str
    root_to_parent_thing_groups: List[RootToParentThingGroup] = Field(..., alias="rootToParentThingGroups")
    attributes: Dict[str, Any]
    dynamic_group_mapping_id: Optional[str] = Field(None, alias="dynamicGroupMappingId")


class IoTCoreAddOrRemoveFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """Thing Added to or Removed from a Thing Group"""

    operation: EVENT_ADD_REMOVE_OPERATION
    account_id: str = Field(..., alias="accountId")
    group_arn: str = Field(..., alias="groupArn")
    group_id: str = Field(..., alias="groupId")
    thing_arn: str = Field(..., alias="thingArn")
    thing_id: str = Field(..., alias="thingId")
    membership_id: str = Field(..., alias="membershipId")


class IoTCoreAddOrDeleteFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """Thing Group Added to or Deleted from a Thing Group"""

    operation: EVENT_ADD_REMOVE_OPERATION
    account_id: str = Field(..., alias="accountId")
    thing_group_id: str = Field(..., alias="thingGroupId")
    thing_group_name: str = Field(..., alias="thingGroupName")
    child_group_id: str = Field(..., alias="childGroupId")
    child_group_name: str = Field(..., alias="childGroupName")

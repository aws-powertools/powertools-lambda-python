from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class IoTCoreRegistryEventsBase(BaseModel):
    eventType: str
    eventId: str
    timestamp: int


EVENT_CRUD_OPERATION = Literal["CREATED", "UPDATED", "DELETED"]
EVENT_ADD_REMOVE_OPERATION = Literal["ADDED", "REMOVED"]


class IoTCoreThingEvent(IoTCoreRegistryEventsBase):
    """The "Thing: created, updated, deleted" event"""

    operation: EVENT_CRUD_OPERATION

    thingId: str
    accountId: str
    thingName: str
    versionNumber: int
    thingTypeName: Optional[str]
    billingGroupName: Optional[str]

    attributes: Dict[str, Any]


class IoTCoreThingTypeEvent(IoTCoreRegistryEventsBase):
    operation: EVENT_CRUD_OPERATION
    accountId: str
    thingTypeId: str
    thingTypeName: str
    isDeprecated: bool
    deprecationDate: Optional[str]
    searchableAttributes: List[str]
    propagatingAttributes: Dict[str, str]
    description: str


class IoTCoreThingTypeAssociationEvent(IoTCoreRegistryEventsBase):
    """
    Thing Type Associated or Disassociated with a Thing
    """

    operation: EVENT_ADD_REMOVE_OPERATION
    thingId: str
    thingName: str
    thingTypeName: str


class RootToParentThingGroup(BaseModel):
    groupArn: str
    groupId: str


class IoTCoreThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    Thing Group Created/Updated/Deleted
    """

    operation: EVENT_CRUD_OPERATION
    accountId: str
    thingGroupId: str
    thingGroupName: str
    versionNumber: int
    parentGroupName: Optional[str]
    parentGroupId: Optional[str]
    description: str
    rootToParentThingGroups: List[RootToParentThingGroup]

    attributes: Dict[str, Any]

    dynamicGroupMappingId: Optional[str]


class IoTCoreAddOrRemoveFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    Thing Added to or Removed from a Thing Group
    """

    operation: EVENT_ADD_REMOVE_OPERATION
    accountId: str
    groupArn: str
    groupId: str
    thingArn: str
    thingId: str
    membershipId: str


class IoTCoreAddOrDeleteFromThingGroupEvent(IoTCoreRegistryEventsBase):
    """
    Thing Group Added to or Deleted from a Thing Group
    """

    operation: EVENT_ADD_REMOVE_OPERATION
    accountId: str
    thingGroupId: str
    thingGroupName: str
    childGroupId: str
    childGroupName: str

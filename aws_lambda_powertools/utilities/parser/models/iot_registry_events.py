import enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class IoTCoreRegistryEventsBase(BaseModel):
    eventType: str
    eventId: str
    timestamp: int


class IoTCRUDEventOperation(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class AddRemoveOperation(str, enum.Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"


class IoTCoreThingEvent(IoTCoreRegistryEventsBase):
    """The "Thing: created, updated, deleted" event"""

    operation: IoTCRUDEventOperation

    thingId: str
    thingName: str
    versionNumber: int
    thingTypeName: Optional[str]
    billingGroupName: Optional[str]

    attributes: Dict[str, Any]


class IoTCoreThingTypeEvent(IoTCoreRegistryEventsBase):
    operation: IoTCRUDEventOperation
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

    operation: AddRemoveOperation
    thingId: str
    thingName: str
    thingTypeName: str


class RootToParentThingGroup(BaseModel):
    groupArn: str
    groupId: str


class IoTThingGroupCRUDEvent(IOTCoreRegistryEventBase):
    """
    Thing Group Created/Updated/Deleted
    """

    operation: IoTCRUDEventOperation
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


class IoTThingAddedToOrRemoveFromThingGroupEvent(IOTCoreRegistryEventBase):
    """
    Thing Added to or Removed from a Thing Group
    """

    operation: AddRemoveOperation
    accountId: str
    groupArn: str
    groupId: str
    thingArn: str
    thingId: str
    membershipId: str


class IoTThingGroupAddedToOrDeletedFromThingGroupEvent(IOTCoreRegistryEventBase):
    """
    Thing Group Added to or Deleted from a Thing Group
    """

    operation: AddRemoveOperation
    accountId: str
    thingGroupId: str
    thingGroupName: str
    childGroupId: str
    childGroupName: str

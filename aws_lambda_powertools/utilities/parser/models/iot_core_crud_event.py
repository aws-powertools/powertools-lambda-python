import enum
from typing import Any, Optional

from pydantic import BaseModel


class IoTCRUDEventOperation(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class IoTCRUDEvent(BaseModel):
    """The "Thing: created, updated, deleted" event"""

    eventType: str
    eventId: str
    timestamp: int

    operation: IoTCRUDEventOperation

    thingId: str

    thingName: str
    versionNumber: int
    thingTypeName: Optional[str]
    billinGroupName: Optional[str]

    attributes: dict[str, Any]

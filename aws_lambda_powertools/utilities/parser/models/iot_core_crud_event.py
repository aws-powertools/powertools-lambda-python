import enum
from typing import Any, Optional

from pydantic import BaseModel


class AWSIoTCRUDEventOperation(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"


class AWSIoTCRUDEvent(BaseModel):
    """The "Thing: created, updated, deleted" eventt"""

    eventType: str
    eventId: str
    timestamp: int

    operation: AWSIoTCRUDEventOperation

    thingId: str

    thingName: str
    versionNumber: int
    thingTypeName: Optional[str]
    billinGroupName: Optional[str]

    attributes: dict[str, Any]

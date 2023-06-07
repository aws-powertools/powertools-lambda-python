from typing_extensions import TypedDict


class TypedLog(TypedDict, total=False):
    level: str
    location: str
    timestamp: str
    service: str
    event: str

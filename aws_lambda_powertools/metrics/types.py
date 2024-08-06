from typing import TypedDict

from typing_extensions import NotRequired


class MetricNameUnitResolution(TypedDict):
    Name: str
    Unit: str
    StorageResolution: NotRequired[int]

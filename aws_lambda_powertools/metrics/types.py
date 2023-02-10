from typing_extensions import NotRequired, TypedDict


class MetricNameUnitResolution(TypedDict):
    Name: str
    Unit: str
    StorageResolution: NotRequired[int]

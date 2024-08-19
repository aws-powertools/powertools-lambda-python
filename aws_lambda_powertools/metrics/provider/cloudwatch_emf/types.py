from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing_extensions import NotRequired


class CloudWatchEMFMetric(TypedDict):
    Name: str
    Unit: str
    StorageResolution: NotRequired[int]


class CloudWatchEMFMetrics(TypedDict):
    Namespace: str
    Dimensions: list[list[str]]  # [ [ 'test_dimension' ] ]
    Metrics: list[CloudWatchEMFMetric]


class CloudWatchEMFRoot(TypedDict):
    Timestamp: int
    CloudWatchMetrics: list[CloudWatchEMFMetrics]


class CloudWatchEMFOutput(TypedDict):
    _aws: CloudWatchEMFRoot

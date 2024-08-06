from typing import List, TypedDict

from typing_extensions import NotRequired


class CloudWatchEMFMetric(TypedDict):
    Name: str
    Unit: str
    StorageResolution: NotRequired[int]


class CloudWatchEMFMetrics(TypedDict):
    Namespace: str
    Dimensions: List[List[str]]  # [ [ 'test_dimension' ] ]
    Metrics: List[CloudWatchEMFMetric]


class CloudWatchEMFRoot(TypedDict):
    Timestamp: int
    CloudWatchMetrics: List[CloudWatchEMFMetrics]


class CloudWatchEMFOutput(TypedDict):
    _aws: CloudWatchEMFRoot

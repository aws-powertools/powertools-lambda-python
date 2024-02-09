from aws_lambda_powertools.shared.types import List, NotRequired, TypedDict


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

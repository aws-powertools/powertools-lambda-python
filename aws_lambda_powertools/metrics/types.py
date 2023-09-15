from aws_lambda_powertools.shared.types import NotRequired, TypedDict


class MetricNameUnitResolution(TypedDict):
    Name: str
    Unit: str
    StorageResolution: NotRequired[int]

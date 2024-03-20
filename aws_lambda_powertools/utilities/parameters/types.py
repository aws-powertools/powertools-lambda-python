from aws_lambda_powertools.shared.types import Literal, TypedDict

TransformOptions = Literal["json", "binary", "auto", None]


class PutParameterResponse(TypedDict):
    Version: int
    Tier: str
    ResponseMetadata: dict

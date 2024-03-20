from aws_lambda_powertools.shared.types import List, Literal, TypedDict

TransformOptions = Literal["json", "binary", "auto", None]


class PutParameterResponse(TypedDict):
    Version: int
    Tier: str
    ResponseMetadata: dict


class SetSecretResponse(TypedDict):
    ARN: str
    Name: str
    VersionId: str
    VersionStages: List[str]

from typing import Any, Optional

from aws_lambda_powertools.shared.types import Dict, List, Literal, TypedDict

TransformOptions = Literal["json", "binary", "auto", None]


class PutParameterResponse(TypedDict):
    Version: int
    Tier: str
    ResponseMetadata: dict


class SetSecretResponse(TypedDict):
    ARN: str
    Name: str
    VersionId: str
    VersionStages: Optional[List[str]]
    ReplicationStatus: Optional[List[Dict[str, Any]]]
    ResponseMetadata: dict

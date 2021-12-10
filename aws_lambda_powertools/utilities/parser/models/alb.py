from typing import Dict, Union

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser.types import Model


class AlbRequestContextData(BaseModel):
    targetGroupArn: str


class AlbRequestContext(BaseModel):
    elb: AlbRequestContextData


class AlbModel(BaseModel):
    httpMethod: str
    path: str
    body: Union[str, Model]
    isBase64Encoded: bool
    headers: Dict[str, str]
    queryStringParameters: Dict[str, str]
    requestContext: AlbRequestContext

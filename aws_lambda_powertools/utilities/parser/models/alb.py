from typing import Dict, Type, Union

from pydantic import BaseModel


class AlbRequestContextData(BaseModel):
    targetGroupArn: str


class AlbRequestContext(BaseModel):
    elb: AlbRequestContextData


class AlbModel(BaseModel):
    httpMethod: str
    path: str
    body: Union[str, Type[BaseModel]]
    isBase64Encoded: bool
    headers: Dict[str, str]
    queryStringParameters: Dict[str, str]
    requestContext: AlbRequestContext

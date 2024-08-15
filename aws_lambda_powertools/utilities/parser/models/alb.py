from __future__ import annotations

from pydantic import BaseModel


class AlbRequestContextData(BaseModel):
    targetGroupArn: str


class AlbRequestContext(BaseModel):
    elb: AlbRequestContextData


class AlbModel(BaseModel):
    httpMethod: str
    path: str
    body: str | type[BaseModel]
    isBase64Encoded: bool
    headers: dict[str, str]
    queryStringParameters: dict[str, str]
    requestContext: AlbRequestContext

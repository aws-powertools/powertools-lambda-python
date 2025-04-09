from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class AppSyncIamIdentity(BaseModel):
    accountId: str
    cognitoIdentityPoolId: Optional[str]
    cognitoIdentityId: Optional[str]
    sourceIp: List[str]
    username: str
    userArn: str
    cognitoIdentityAuthType: Optional[str]
    cognitoIdentityAuthProvider: Optional[str]


class AppSyncCognitoIdentity(BaseModel):
    sub: str
    issuer: str
    username: str
    claims: Dict[str, Any]
    sourceIp: List[str]
    defaultAuthStrategy: str
    groups: Optional[List[str]]


class AppSyncOidcIdentity(BaseModel):
    claims: Dict[str, Any]
    issuer: str
    sub: str


class AppSyncLambdaIdentity(BaseModel):
    resolverContext: Dict[str, Any]


AppSyncIdentity = Union[
    AppSyncIamIdentity,
    AppSyncCognitoIdentity,
    AppSyncOidcIdentity,
    AppSyncLambdaIdentity,
]


class AppSyncRequestModel(BaseModel):
    domainName: Optional[str]
    headers: Dict[str, str]


class AppSyncInfoModel(BaseModel):
    selectionSetList: List[str]
    selectionSetGraphQL: str
    parentTypeName: str
    fieldName: str
    variables: Dict[str, Any]


class AppSyncPrevModel(BaseModel):
    result: Dict[str, Any]


class AppSyncResolverEventModel(BaseModel):
    arguments: Dict[str, Any]
    identity: Optional[AppSyncIdentity]
    source: Optional[Dict[str, Any]]
    request: AppSyncRequestModel
    info: AppSyncInfoModel
    prev: Optional[AppSyncPrevModel]
    stash: Dict[str, Any]


AppSyncBatchResolverEventModel = List[AppSyncResolverEventModel]

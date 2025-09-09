from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AppSyncIamIdentity(BaseModel):
    accountId: str = Field(description="The AWS account ID of the caller.", examples=["123456789012"])
    cognitoIdentityPoolId: Optional[str] = Field(
        default=None,
        description="The Amazon Cognito identity pool ID associated with the caller.",
        examples=["us-east-1:12345678-1234-1234-1234-123456789012"],
    )
    cognitoIdentityId: Optional[str] = Field(
        default=None,
        description="The Amazon Cognito identity ID of the caller.",
        examples=["us-east-1:12345678-1234-1234-1234-123456789012"],
    )
    sourceIp: List[str] = Field(
        description=(
            "The source IP address of the caller that AWS AppSync receives. "
            "If the request includes a x-forwarded-for header, this is a list of IP addresses."
        ),
    )
    username: str = Field(
        description="The IAM user principal name.",
        examples=["AIDAJEXAMPLE1234", "appsync-user"],
    )
    userArn: str = Field(
        description="The Amazon Resource Name (ARN) of the IAM user.",
        examples=["arn:aws:iam::123456789012:user/appsync", "arn:aws:iam::123456789012:user/service-user"],
    )
    cognitoIdentityAuthType: Optional[str] = Field(
        default=None,
        description="Either authenticated or unauthenticated based on the identity type.",
        examples=["authenticated", "unauthenticated"],
    )
    cognitoIdentityAuthProvider: Optional[str] = Field(
        default=None,
        description=(
            "A comma-separated list of external identity provider information "
            "used in obtaining the credentials used to sign the request."
        ),
        examples=[
            "cognito-idp.us-east-1.amazonaws.com/us-east-1_POOL_ID",
            "graph.facebook.com,cognito-idp.us-east-1.amazonaws.com/us-east-1_POOL_ID",
        ],
    )


class AppSyncCognitoIdentity(BaseModel):
    sub: str = Field(
        description="The UUID of the authenticated user from Cognito User Pool.",
        examples=["user-uuid-1234-5678-9012-123456789012", "user-uuid-abcd-efgh-ijkl-mnopqrstuvwx"],
    )
    issuer: str = Field(
        description="The token issuer URL from Cognito User Pool.",
        examples=[
            "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_POOL_ID",
            "https://cognito-idp.us-west-2.amazonaws.com/us-west-xxxxxxxxxxx",
        ],
    )
    username: str = Field(
        description="The username of the authenticated user (cognito:username attribute).",
        examples=["mike", "jdoe", "user123"],
    )
    claims: Dict[str, Any] = Field(description="The JWT claims that the user has from Cognito User Pool.")
    sourceIp: List[str] = Field(
        description=(
            "The source IP address of the caller that AWS AppSync receives. "
            "If the request includes a x-forwarded-for header, this is a list of IP addresses."
        ),
    )
    defaultAuthStrategy: str = Field(
        description="The default authorization strategy for this caller (ALLOW or DENY).",
        examples=["ALLOW", "DENY"],
    )
    groups: Optional[List[str]] = Field(
        default=None,
        description="The Cognito User Pool groups that the user belongs to.",
        examples=[["admin", "users"], ["developers"]],
    )


class AppSyncOidcIdentity(BaseModel):
    claims: Dict[str, Any] = Field(description="The JWT claims from the OpenID Connect provider.")
    issuer: str = Field(
        description="The token issuer URL from the OpenID Connect provider.",
        examples=["https://accounts.google.com", "https://login.microsoftonline.com/tenant-id/v2.0"],
    )
    sub: str = Field(
        description="The subject identifier from the OpenID Connect provider.",
        examples=["248289761001", "provider-subject-identifier"],
    )


class AppSyncLambdaIdentity(BaseModel):
    resolverContext: Dict[str, Any] = Field(
        description=(
            "The resolver context returned by the Lambda function authorizing the request. "
            "Contains custom authorization data from AWS_LAMBDA authorization."
        ),
        examples=[
            {"userId": "user123", "role": "admin", "permissions": ["read", "write"]},
            {"customClaim": "value", "authLevel": "premium"},
        ],
    )


AppSyncIdentity = Union[
    AppSyncIamIdentity,
    AppSyncCognitoIdentity,
    AppSyncOidcIdentity,
    AppSyncLambdaIdentity,
]


class AppSyncRequestModel(BaseModel):
    domainName: Optional[str] = Field(
        default=None,
        description=(
            "The custom domain name used to access the GraphQL endpoint. "
            "Returns null when using the default GraphQL endpoint domain name."
        ),
        examples=["api.example.com", "graphql.mycompany.com"],
    )
    headers: Dict[str, str] = Field(
        description="HTTP headers from the GraphQL request, including custom headers.",
        examples=[
            {
                "cloudfront-viewer-country": "US",
                "host": "example.appsync-api.us-east-1.amazonaws.com",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "content-type": "application/json",
            },
        ],
    )


class AppSyncInfoModel(BaseModel):
    selectionSetList: List[str] = Field(
        description=(
            "A list representation of the fields in the GraphQL selection set. "
            "Fields that are aliased are referenced only by the alias name."
        ),
        examples=[["id", "field1", "field2"], ["postId", "title", "content", "author", "author/id", "author/name"]],
    )
    selectionSetGraphQL: str = Field(
        description=(
            "A string representation of the selection set, formatted as GraphQL SDL. "
            "Inline fragments are preserved but fragments are not merged."
        ),
        examples=[
            "{\n  id\n  field1\n  field2\n}",
            "{\n  postId\n  title\n  content\n  author {\n    id\n    name\n  }\n}",
        ],
    )
    parentTypeName: str = Field(
        description="The name of the parent type for the field that is currently being resolved.",
        examples=["Query", "Mutation", "Subscription", "User", "Post"],
    )
    fieldName: str = Field(
        description="The name of the field that is currently being resolved.",
        examples=["getUser", "createPost", "locations", "updateProfile"],
    )
    variables: Dict[str, Any] = Field(
        description="A map which holds all variables that are passed into the GraphQL request.",
        examples=[{"userId": "123", "limit": 10}, {"input": {"name": "John", "email": "john@example.com"}}, {}],
    )


class AppSyncPrevModel(BaseModel):
    result: Dict[str, Any] = Field(
        description=(
            "The result of whatever previous operation was executed in a pipeline resolver. "
            "Contains the output from the previous function or Before mapping template."
        ),
        examples=[
            {"userId": "123", "posts": [{"id": "1", "title": "Hello World"}]},
            {"data": {"field1": "value1", "field2": "value2"}},
        ],
    )


class AppSyncResolverEventModel(BaseModel):
    arguments: Dict[str, Any] = Field(
        description="The arguments passed to the GraphQL field.",
        examples=[
            {"id": "123", "limit": 10},
            {"input": {"name": "John", "email": "john@example.com"}},
            {"page": 2, "size": 1, "name": "value"},
        ],
    )
    identity: Optional[AppSyncIdentity] = Field(
        default=None,
        description="Information about the caller identity (authenticated user or API key).",
    )
    source: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The parent object for the field. For top-level fields, this will be null.",
        examples=[
            None,
            {"id": "user123", "name": "John Doe"},
            {"name": "Value", "nested": {"name": "value", "list": []}},
            {"postId": "post456", "title": "My Post"},
        ],
    )
    request: AppSyncRequestModel = Field(description="Information about the GraphQL request context.")
    info: AppSyncInfoModel = Field(
        description="Information about the GraphQL request including selection set and field details.",
    )
    prev: Optional[AppSyncPrevModel] = Field(
        default=None,
        description="Results from the previous resolver in a pipeline resolver.",
    )
    stash: Dict[str, Any] = Field(
        description=(
            "The stash is a map that is made available inside each resolver and function mapping template. "
            "The same stash instance lives through a single resolver execution."
        ),
        examples=[{"customData": "value", "userId": "123"}],
    )


AppSyncBatchResolverEventModel = List[AppSyncResolverEventModel]

from pydantic import BaseModel, Field


class AlbRequestContextData(BaseModel):
    targetGroupArn: str = Field(
        description="The ARN of the target group that the request was routed to.",
        examples=[
            "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/73e2d6bc24d8a067",
            "arn:aws:elasticloadbalancing:eu-west-1:123456789012:targetgroup/api-targets/1234567890123456",
        ],
    )


class AlbRequestContext(BaseModel):
    elb: AlbRequestContextData = Field(
        description="Information about the Elastic Load Balancer that processed the request.",
    )


class AlbModel(BaseModel):
    httpMethod: str = Field(
        description="The HTTP method used for the request.",
        examples=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "CONNECT"],
    )
    path: str = Field(
        description="The path portion of the request URL.",
        examples=["/", "/api/users", "/health", "/api/v1/products/123"],
    )
    body: str | type[BaseModel] = Field(
        description="The request body. Can be a string or a parsed model if content-type allows parsing.",
    )
    isBase64Encoded: bool = Field(description="Indicates whether the body is base64-encoded.", examples=[False, True])
    # ALB sends either headers and queryStringParameters, or the two multi-value fields, depending on
    # the target group's multi-value headers setting. The ones it leaves out are empty dicts, like in ALBEvent.
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="The request headers as key-value pairs. Empty when multi-value headers are enabled.",
        examples=[
            {"host": "example.com", "user-agent": "Mozilla/5.0"},
            {"content-type": "application/json", "authorization": "Bearer token123"},
        ],
    )
    queryStringParameters: dict[str, str] = Field(
        default_factory=dict,
        description="The query string parameters as key-value pairs. Empty when multi-value headers are enabled.",
        examples=[{"page": "1", "limit": "10"}, {"filter": "active", "sort": "name"}],
    )
    multiValueHeaders: dict[str, list[str]] = Field(
        default_factory=dict,
        description="The request headers with all their values. Only sent when multi-value headers are enabled.",
        examples=[
            {"host": ["example.com"], "cookie": ["name1=value1", "name2=value2"]},
        ],
    )
    multiValueQueryStringParameters: dict[str, list[str]] = Field(
        default_factory=dict,
        description=(
            "The query string parameters with all their values. Only sent when multi-value headers are enabled."
        ),
        examples=[{"myKey": ["val1", "val2"]}],
    )
    requestContext: AlbRequestContext = Field(
        description="Contains information about the request context, including the load balancer details.",
    )

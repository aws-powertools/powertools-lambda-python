from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, Field

from aws_lambda_powertools.event_handler.openapi.compat import model_rebuild
from aws_lambda_powertools.event_handler.openapi.constants import (
    MODEL_CONFIG_ALLOW,
    MODEL_CONFIG_IGNORE,
)

"""
The code defines Pydantic models for the various OpenAPI objects like OpenAPI, PathItem, Operation, Parameter etc.
These models can be used to parse OpenAPI JSON/YAML files into Python objects, or generate OpenAPI from Python data.
"""


# https://swagger.io/specification/#contact-object
class Contact(BaseModel):
    name: str | None = None
    url: AnyUrl | None = None
    email: str | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#license-object
class License(BaseModel):
    name: str
    identifier: str | None = None
    url: AnyUrl | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#info-object
class Info(BaseModel):
    title: str
    description: str | None = None
    termsOfService: str | None = None
    contact: Contact | None = None
    license: License | None = None  # noqa: A003
    version: str
    summary: str | None = None

    model_config = MODEL_CONFIG_IGNORE


# https://swagger.io/specification/#server-variable-object
class ServerVariable(BaseModel):
    enum: list[str] | None = Field(default=None, min_length=1)
    default: str
    description: str | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#server-object
class Server(BaseModel):
    url: AnyUrl | str
    description: str | None = None
    variables: dict[str, ServerVariable] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#reference-object
class Reference(BaseModel):
    ref: str = Field(alias="$ref")


# https://swagger.io/specification/#discriminator-object
class Discriminator(BaseModel):
    propertyName: str
    mapping: dict[str, str] | None = None


# https://swagger.io/specification/#xml-object
class XML(BaseModel):
    name: str | None = None
    namespace: str | None = None
    prefix: str | None = None
    attribute: bool | None = None
    wrapped: bool | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#external-documentation-object
class ExternalDocumentation(BaseModel):
    description: str | None = None
    url: AnyUrl

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#schema-object
class Schema(BaseModel):
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-the-json-schema-core-vocabu
    # Core Vocabulary
    schema_: str | None = Field(default=None, alias="$schema")
    vocabulary: str | None = Field(default=None, alias="$vocabulary")
    id: str | None = Field(default=None, alias="$id")  # noqa: A003
    anchor: str | None = Field(default=None, alias="$anchor")
    dynamicAnchor: str | None = Field(default=None, alias="$dynamicAnchor")
    ref: str | None = Field(default=None, alias="$ref")
    dynamicRef: str | None = Field(default=None, alias="$dynamicRef")
    defs: dict[str, SchemaOrBool] | None = Field(default=None, alias="$defs")
    comment: str | None = Field(default=None, alias="$comment")
    # Ref: JSON Schema 2020-12: https://json-schema.org/draft/2020-12/json-schema-core.html#name-a-vocabulary-for-applying-s
    # A Vocabulary for Applying Subschemas
    allOf: list[SchemaOrBool] | None = None
    anyOf: list[SchemaOrBool] | None = None
    oneOf: list[SchemaOrBool] | None = None
    not_: SchemaOrBool | None = Field(default=None, alias="not")
    if_: SchemaOrBool | None = Field(default=None, alias="if")
    then: SchemaOrBool | None = None
    else_: SchemaOrBool | None = Field(default=None, alias="else")
    dependentSchemas: dict[str, SchemaOrBool] | None = None
    prefixItems: list[SchemaOrBool] | None = None
    # MAINTENANCE: uncomment and remove below when deprecating Pydantic v1
    # MAINTENANCE: It generates a list of schemas for tuples, before prefixItems was available
    # MAINTENANCE: items: SchemaOrBool | None = None
    items: SchemaOrBool | list[SchemaOrBool] | None = None
    contains: SchemaOrBool | None = None
    properties: dict[str, SchemaOrBool] | None = None
    patternProperties: dict[str, SchemaOrBool] | None = None
    additionalProperties: SchemaOrBool | None = None
    propertyNames: SchemaOrBool | None = None
    unevaluatedItems: SchemaOrBool | None = None
    unevaluatedProperties: SchemaOrBool | None = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-structural
    # A Vocabulary for Structural Validation
    type: str | None = None  # noqa: A003
    enum: list[Any] | None = None
    const: Any | None = None
    multipleOf: float | None = Field(default=None, gt=0)
    maximum: float | None = None
    exclusiveMaximum: float | None = None
    minimum: float | None = None
    exclusiveMinimum: float | None = None
    maxLength: int | None = Field(default=None, ge=0)
    minLength: int | None = Field(default=None, ge=0)
    pattern: str | None = None
    maxItems: int | None = Field(default=None, ge=0)
    minItems: int | None = Field(default=None, ge=0)
    uniqueItems: bool | None = None
    maxContains: int | None = Field(default=None, ge=0)
    minContains: int | None = Field(default=None, ge=0)
    maxProperties: int | None = Field(default=None, ge=0)
    minProperties: int | None = Field(default=None, ge=0)
    required: list[str] | None = None
    dependentRequired: dict[str, set[str]] | None = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-vocabularies-for-semantic-c
    # Vocabularies for Semantic Content With "format"
    format: str | None = None  # noqa: A003
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-the-conten
    # A Vocabulary for the Contents of String-Encoded Data
    contentEncoding: str | None = None
    contentMediaType: str | None = None
    contentSchema: SchemaOrBool | None = None
    # Ref: JSON Schema Validation 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    # A Vocabulary for Basic Meta-Data Annotations
    title: str | None = None
    description: str | None = None
    default: Any | None = None
    deprecated: bool | None = None
    readOnly: bool | None = None
    writeOnly: bool | None = None
    examples: list[Example] | None = None
    # Ref: OpenAPI 3.0.0: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.0.md#schema-object
    # Schema Object
    discriminator: Discriminator | None = None
    xml: XML | None = None
    externalDocs: ExternalDocumentation | None = None

    model_config = MODEL_CONFIG_ALLOW


# Ref: https://json-schema.org/draft/2020-12/json-schema-core.html#name-json-schema-documents
# A JSON Schema MUST be an object or a boolean.
SchemaOrBool = Schema | bool


# https://swagger.io/specification/#example-object
class Example(BaseModel):
    summary: str | None = None
    description: str | None = None
    value: Any | None = None
    externalValue: AnyUrl | None = None

    model_config = MODEL_CONFIG_ALLOW


class ParameterInType(Enum):
    query = "query"
    header = "header"
    path = "path"
    cookie = "cookie"


# https://swagger.io/specification/#encoding-object
class Encoding(BaseModel):
    contentType: str | None = None
    headers: dict[str, Header | Reference] | None = None
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#media-type-object
class MediaType(BaseModel):
    schema_: Schema | Reference | None = Field(default=None, alias="schema")
    examples: dict[str, Example | Reference] | None = None
    encoding: dict[str, Encoding] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#parameter-object
class ParameterBase(BaseModel):
    description: str | None = None
    required: bool | None = None
    deprecated: bool | None = None
    # Serialization rules for simple scenarios
    style: str | None = None
    explode: bool | None = None
    allowReserved: bool | None = None
    schema_: Schema | Reference | None = Field(default=None, alias="schema")
    examples: dict[str, Example | Reference] | None = None
    # Serialization rules for more complex scenarios
    content: dict[str, MediaType] | None = None

    model_config = MODEL_CONFIG_ALLOW


class Parameter(ParameterBase):
    name: str
    in_: ParameterInType = Field(alias="in")


class Header(ParameterBase):
    pass


# https://swagger.io/specification/#request-body-object
class RequestBody(BaseModel):
    description: str | None = None
    content: dict[str, MediaType]
    required: bool | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#link-object
class Link(BaseModel):
    operationRef: str | None = None
    operationId: str | None = None
    parameters: dict[str, Any | str] | None = None
    requestBody: Any | str | None = None
    description: str | None = None
    server: Server | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#response-object
class Response(BaseModel):
    description: str
    headers: dict[str, Header | Reference] | None = None
    content: dict[str, MediaType] | None = None
    links: dict[str, Link | Reference] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#tag-object
class Tag(BaseModel):
    name: str
    description: str | None = None
    externalDocs: ExternalDocumentation | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#operation-object
class Operation(BaseModel):
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    externalDocs: ExternalDocumentation | None = None
    operationId: str | None = None
    parameters: list[Parameter | Reference] | None = None
    requestBody: RequestBody | Reference | None = None
    # Using Any for Specification Extensions
    responses: dict[int, Response | Any] | None = None
    callbacks: dict[str, dict[str, PathItem] | Reference] | None = None
    deprecated: bool | None = None
    security: list[dict[str, list[str]]] | None = None
    servers: list[Server] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#path-item-object
class PathItem(BaseModel):
    ref: str | None = Field(default=None, alias="$ref")
    summary: str | None = None
    description: str | None = None
    get: Operation | None = None
    put: Operation | None = None
    post: Operation | None = None
    delete: Operation | None = None
    options: Operation | None = None
    head: Operation | None = None
    patch: Operation | None = None
    trace: Operation | None = None
    servers: list[Server] | None = None
    parameters: list[Parameter | Reference] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#security-scheme-object
class SecuritySchemeType(Enum):
    apiKey = "apiKey"
    http = "http"
    oauth2 = "oauth2"
    openIdConnect = "openIdConnect"


class SecurityBase(BaseModel):
    type_: SecuritySchemeType = Field(alias="type")
    description: str | None = None

    model_config = {"extra": "allow", "populate_by_name": True}


class APIKeyIn(Enum):
    query = "query"
    header = "header"
    cookie = "cookie"


class APIKey(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.apiKey, alias="type")
    in_: APIKeyIn = Field(alias="in")
    name: str


class HTTPBase(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.http, alias="type")
    scheme: str


class HTTPBearer(HTTPBase):
    scheme: Literal["bearer"] = "bearer"
    bearerFormat: str | None = None


class OAuthFlow(BaseModel):
    refreshUrl: str | None = None
    scopes: dict[str, str] = {}

    model_config = MODEL_CONFIG_ALLOW


class OAuthFlowImplicit(OAuthFlow):
    authorizationUrl: str


class OAuthFlowPassword(OAuthFlow):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlow):
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlow):
    authorizationUrl: str
    tokenUrl: str


class OAuthFlows(BaseModel):
    implicit: OAuthFlowImplicit | None = None
    password: OAuthFlowPassword | None = None
    clientCredentials: OAuthFlowClientCredentials | None = None
    authorizationCode: OAuthFlowAuthorizationCode | None = None

    model_config = MODEL_CONFIG_ALLOW


class OAuth2(SecurityBase):
    type_: SecuritySchemeType = Field(default=SecuritySchemeType.oauth2, alias="type")
    flows: OAuthFlows


class OpenIdConnect(SecurityBase):
    type_: SecuritySchemeType = Field(
        default=SecuritySchemeType.openIdConnect,
        alias="type",
    )
    openIdConnectUrl: str


SecurityScheme = APIKey | HTTPBase | OAuth2 | OpenIdConnect | HTTPBearer


# https://swagger.io/specification/#components-object
class Components(BaseModel):
    schemas: dict[str, Schema | Reference] | None = None
    responses: dict[str, Response | Reference] | None = None
    parameters: dict[str, Parameter | Reference] | None = None
    examples: dict[str, Example | Reference] | None = None
    requestBodies: dict[str, RequestBody | Reference] | None = None
    headers: dict[str, Header | Reference] | None = None
    securitySchemes: dict[str, SecurityScheme | Reference] | None = None
    links: dict[str, Link | Reference] | None = None
    # Using Any for Specification Extensions
    callbacks: dict[str, dict[str, PathItem] | Reference | Any] | None = None
    pathItems: dict[str, PathItem | Reference] | None = None

    model_config = MODEL_CONFIG_ALLOW


# https://swagger.io/specification/#openapi-object
class OpenAPI(BaseModel):
    openapi: str
    info: Info
    jsonSchemaDialect: str | None = None
    servers: list[Server] | None = None
    # Using Any for Specification Extensions
    paths: dict[str, PathItem | Any] | None = None
    webhooks: dict[str, PathItem | Reference] | None = None
    components: Components | None = None
    security: list[dict[str, list[str]]] | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None

    model_config = MODEL_CONFIG_ALLOW


model_rebuild(Schema)
model_rebuild(Operation)
model_rebuild(Encoding)

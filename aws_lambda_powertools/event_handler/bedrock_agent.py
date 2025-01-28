from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

from typing_extensions import override

from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import (
    _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
    ProxyEventType,
    ResponseBuilder,
)
from aws_lambda_powertools.event_handler.openapi.constants import DEFAULT_API_VERSION, DEFAULT_OPENAPI_VERSION

if TYPE_CHECKING:
    from re import Match

    from aws_lambda_powertools.event_handler.openapi.models import Contact, License, SecurityScheme, Server, Tag
    from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
    from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent


class BedrockResponseBuilder(ResponseBuilder):
    """
    Bedrock Response Builder. This builds the response dict to be returned by Lambda when using Bedrock Agents.

    Since the payload format is different from the standard API Gateway Proxy event, we override the build method.
    """

    @override
    def build(self, event: BedrockAgentEvent, *args) -> dict[str, Any]:
        """Build the full response dict to be returned by the lambda"""
        self._route(event, None)

        body = self.response.body
        if self.response.is_json() and not isinstance(self.response.body, str):
            body = self.serializer(self.response.body)

        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.action_group,
                "apiPath": event.api_path,
                "httpMethod": event.http_method,
                "httpStatusCode": self.response.status_code,
                "responseBody": {
                    self.response.content_type: {
                        "body": body,
                    },
                },
            },
        }


class BedrockAgentResolver(ApiGatewayResolver):
    """Bedrock Agent Resolver

    See https://aws.amazon.com/bedrock/agents/ for more information.

    Examples
    --------
    Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

    ```python
    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.event_handler import BedrockAgentResolver

    tracer = Tracer()
    app = BedrockAgentResolver()

    @app.get("/claims")
    def simple_get():
        return "You have 3 claims"

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```

    """

    current_event: BedrockAgentEvent

    def __init__(self, debug: bool = False, enable_validation: bool = True):
        super().__init__(
            proxy_type=ProxyEventType.BedrockAgentEvent,
            cors=None,
            debug=debug,
            serializer=None,
            strip_prefixes=None,
            enable_validation=enable_validation,
        )
        self._response_builder_class = BedrockResponseBuilder

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def get(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        openapi_extensions = None
        security = None

        return super().get(
            rule,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def post(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ):
        openapi_extensions = None
        security = None

        return super().post(
            rule,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def put(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ):
        openapi_extensions = None
        security = None

        return super().put(
            rule,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def patch(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        deprecated: bool = False,
        middlewares: list[Callable] | None = None,
    ):
        openapi_extensions = None
        security = None

        return super().patch(
            rule,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def delete(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: bool | None = None,
        compress: bool = False,
        cache_control: str | None = None,
        summary: str | None = None,
        responses: dict[int, OpenAPIResponse] | None = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: list[str] | None = None,
        operation_id: str | None = None,
        include_in_schema: bool = True,
        deprecated: bool = False,
        middlewares: list[Callable[..., Any]] | None = None,
    ):
        openapi_extensions = None
        security = None

        return super().delete(
            rule,
            cors,
            compress,
            cache_control,
            summary,
            description,
            responses,
            response_description,
            tags,
            operation_id,
            include_in_schema,
            security,
            openapi_extensions,
            deprecated,
            middlewares,
        )

    @override
    def _convert_matches_into_route_keys(self, match: Match) -> dict[str, str]:
        # In Bedrock Agents, all the parameters come inside the "parameters" key, not on the apiPath
        # So we have to search for route parameters in the parameters key
        parameters: dict[str, str] = {}
        if match.groupdict() and self.current_event.parameters:
            parameters = {parameter["name"]: parameter["value"] for parameter in self.current_event.parameters}
        return parameters

    @override
    def get_openapi_json_schema(  # type: ignore[override]
        self,
        *,
        title: str = "Powertools API",
        version: str = DEFAULT_API_VERSION,
        openapi_version: str = DEFAULT_OPENAPI_VERSION,
        summary: str | None = None,
        description: str | None = None,
        tags: list[Tag | str] | None = None,
        servers: list[Server] | None = None,
        terms_of_service: str | None = None,
        contact: Contact | None = None,
        license_info: License | None = None,
        security_schemes: dict[str, SecurityScheme] | None = None,
        security: list[dict[str, list[str]]] | None = None,
    ) -> str:
        """
        Returns the OpenAPI schema as a JSON serializable dict.
        Since Bedrock Agents only support OpenAPI 3.0.0, we convert OpenAPI 3.1.0 schemas
        and enforce 3.0.0 compatibility for seamless integration.

        Parameters
        ----------
        title: str
            The title of the application.
        version: str
            The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
        openapi_version: str, default = "3.0.0"
            The version of the OpenAPI Specification (which the document uses).
        summary: str, optional
            A short summary of what the application does.
        description: str, optional
            A verbose explanation of the application behavior.
        tags: list[Tag, str], optional
            A list of tags used by the specification with additional metadata.
        servers: list[Server], optional
            An array of Server Objects, which provide connectivity information to a target server.
        terms_of_service: str, optional
            A URL to the Terms of Service for the API. MUST be in the format of a URL.
        contact: Contact, optional
            The contact information for the exposed API.
        license_info: License, optional
            The license information for the exposed API.
        security_schemes: dict[str, SecurityScheme]], optional
            A declaration of the security schemes available to be used in the specification.
        security: list[dict[str, list[str]]], optional
            A declaration of which security mechanisms are applied globally across the API.

        Returns
        -------
        str
            The OpenAPI schema as a JSON serializable dict.
        """
        from aws_lambda_powertools.event_handler.openapi.compat import model_json

        openapi_extensions = None

        schema = super().get_openapi_schema(
            title=title,
            version=version,
            openapi_version=openapi_version,
            summary=summary,
            description=description,
            tags=tags,
            servers=servers,
            terms_of_service=terms_of_service,
            contact=contact,
            license_info=license_info,
            security_schemes=security_schemes,
            security=security,
            openapi_extensions=openapi_extensions,
        )
        schema.openapi = "3.0.3"

        # Transform OpenAPI 3.1 into 3.0
        def inner(yaml_dict):
            if isinstance(yaml_dict, dict):
                if "anyOf" in yaml_dict and isinstance((anyOf := yaml_dict["anyOf"]), list):
                    for i, item in enumerate(anyOf):
                        if isinstance(item, dict) and item.get("type") == "null":
                            anyOf.pop(i)
                            yaml_dict["nullable"] = True
                if "examples" in yaml_dict:
                    examples = yaml_dict["examples"]
                    del yaml_dict["examples"]
                    if isinstance(examples, list) and len(examples):
                        yaml_dict["example"] = examples[0]
                for value in yaml_dict.values():
                    inner(value)
            elif isinstance(yaml_dict, list):
                for item in yaml_dict:
                    inner(item)

        model = json.loads(
            model_json(
                schema,
                by_alias=True,
                exclude_none=True,
                indent=2,
            ),
        )

        inner(model)

        return json.dumps(model)

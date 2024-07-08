from re import Match
from typing import Any, Callable, Dict, List, Optional

from typing_extensions import override

from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import (
    _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
    ProxyEventType,
    ResponseBuilder,
)
from aws_lambda_powertools.event_handler.openapi.types import OpenAPIResponse
from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent


class BedrockResponseBuilder(ResponseBuilder):
    """
    Bedrock Response Builder. This builds the response dict to be returned by Lambda when using Bedrock Agents.

    Since the payload format is different from the standard API Gateway Proxy event, we override the build method.
    """

    @override
    def build(self, event: BedrockAgentEvent, *args) -> Dict[str, Any]:
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
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
        summary: Optional[str] = None,
        responses: Optional[Dict[int, OpenAPIResponse]] = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        middlewares: Optional[List[Callable[..., Any]]] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:

        openapi_extensions = None
        security = None

        return super(BedrockAgentResolver, self).get(
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
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def post(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
        summary: Optional[str] = None,
        responses: Optional[Dict[int, OpenAPIResponse]] = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        middlewares: Optional[List[Callable[..., Any]]] = None,
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
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def put(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
        summary: Optional[str] = None,
        responses: Optional[Dict[int, OpenAPIResponse]] = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        middlewares: Optional[List[Callable[..., Any]]] = None,
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
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def patch(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
        summary: Optional[str] = None,
        responses: Optional[Dict[int, OpenAPIResponse]] = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        middlewares: Optional[List[Callable]] = None,
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
            middlewares,
        )

    # Note: we need ignore[override] because we are making the optional `description` field required.
    @override
    def delete(  # type: ignore[override]
        self,
        rule: str,
        description: str,
        cors: Optional[bool] = None,
        compress: bool = False,
        cache_control: Optional[str] = None,
        summary: Optional[str] = None,
        responses: Optional[Dict[int, OpenAPIResponse]] = None,
        response_description: str = _DEFAULT_OPENAPI_RESPONSE_DESCRIPTION,
        tags: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        include_in_schema: bool = True,
        middlewares: Optional[List[Callable[..., Any]]] = None,
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
            middlewares,
        )

    @override
    def _convert_matches_into_route_keys(self, match: Match) -> Dict[str, str]:
        # In Bedrock Agents, all the parameters come inside the "parameters" key, not on the apiPath
        # So we have to search for route parameters in the parameters key
        parameters: Dict[str, str] = {}
        if match.groupdict() and self.current_event.parameters:
            parameters = {parameter["name"]: parameter["value"] for parameter in self.current_event.parameters}
        return parameters

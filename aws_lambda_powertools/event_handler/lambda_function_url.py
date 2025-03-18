from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Pattern

from aws_lambda_powertools.event_handler.api_gateway import (
    ApiGatewayResolver,
    ProxyEventType,
)

if TYPE_CHECKING:
    from http import HTTPStatus

    from aws_lambda_powertools.event_handler import CORSConfig
    from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent


class LambdaFunctionUrlResolver(ApiGatewayResolver):
    """AWS Lambda Function URL resolver

    Notes:
    -----
    Lambda Function URL follows the API Gateway HTTP APIs Payload Format Version 2.0.

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads

    Examples
    --------
    Simple example integrating with Tracer

    ```python
    from aws_lambda_powertools import Tracer
    from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver

    tracer = Tracer()
    app = LambdaFunctionUrlResolver()

    @app.get("/get-call")
    def simple_get():
        return {"message": "Foo"}

    @app.post("/post-call")
    def simple_post():
        post_data: dict = app.current_event.json_body
        return {"message": post_data}

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    """

    current_event: LambdaFunctionUrlEvent

    def __init__(
        self,
        cors: CORSConfig | None = None,
        debug: bool | None = None,
        serializer: Callable[[dict], str] | None = None,
        strip_prefixes: list[str | Pattern] | None = None,
        enable_validation: bool = False,
        response_validation_error_http_code: HTTPStatus | int | None = None,
    ):
        super().__init__(
            ProxyEventType.LambdaFunctionUrlEvent,
            cors,
            debug,
            serializer,
            strip_prefixes,
            enable_validation,
            response_validation_error_http_code,
        )

    def _get_base_path(self) -> str:
        stage = self.current_event.request_context.stage
        if stage and stage != "$default" and self.current_event.request_context.http.method.startswith(f"/{stage}"):
            return f"/{stage}"
        return ""

from typing import Callable, Dict, List, Optional

from aws_lambda_powertools.event_handler import CORSConfig
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver, ProxyEventType
from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent


class LambdaFunctionUrlResolver(ApiGatewayResolver):
    """AWS Lambda Function URL resolver

    Notes:
    -----
    For now, this seems to work the same way as API Gateway HTTP APIs Payload Format Version 2.0.

    Documentation:
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-configuration.html
    - https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads

    Examples
    --------
    Simple example with a custom lambda handler using the Tracer capture_lambda_handler decorator

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
        return {"message": post_data["value"]}

    @tracer.capture_lambda_handler
    def lambda_handler(event, context):
        return app.resolve(event, context)
    """

    current_event: LambdaFunctionUrlEvent

    def __init__(
        self,
        cors: Optional[CORSConfig] = None,
        debug: Optional[bool] = None,
        serializer: Optional[Callable[[Dict], str]] = None,
        strip_prefixes: Optional[List[str]] = None,
    ):
        super().__init__(ProxyEventType.LambdaFunctionUrlEvent, cors, debug, serializer, strip_prefixes)

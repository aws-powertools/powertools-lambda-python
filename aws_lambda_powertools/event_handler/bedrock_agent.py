import logging
from typing import Any, Dict, Optional, cast

from aws_lambda_powertools.event_handler import ApiGatewayResolver
from aws_lambda_powertools.event_handler.api_gateway import CORSConfig, ProxyEventType, ResponseBuilder
from aws_lambda_powertools.utilities.data_classes import BedrockAgentEvent
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent

logger = logging.getLogger(__name__)


class BedrockResponseBuilder(ResponseBuilder):
    def build(self, event: BaseProxyEvent, cors: Optional[CORSConfig] = None) -> Dict[str, Any]:
        """Build the full response dict to be returned by the lambda"""
        self._route(event, cors)

        bedrock_event = cast(BedrockAgentEvent, event)

        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": bedrock_event.action_group,
                "apiPath": bedrock_event.api_path,
                "httpMethod": bedrock_event.http_method,
                "httpStatusCode": self.response.status_code,
                "responseBody": {
                    "application/json": {
                        "body": self.response.body,
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
    """

    current_event: BedrockAgentEvent

    def __init__(self, debug: bool = False, enable_validation: bool = True):
        super().__init__(
            ProxyEventType.BedrockAgentEvent,
            None,
            debug,
            None,
            None,
            enable_validation,
        )
        self.response_builder_class = BedrockResponseBuilder

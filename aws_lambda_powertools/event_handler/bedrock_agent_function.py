from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from aws_lambda_powertools.event_handler.api_gateway import Response, ResponseBuilder

if TYPE_CHECKING:
    from collections.abc import Callable

from enum import Enum

from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent


class ResponseState(Enum):
    FAILURE = "FAILURE"
    REPROMPT = "REPROMPT"


class BedrockFunctionsResponseBuilder(ResponseBuilder):
    """
    Bedrock Functions Response Builder. This builds the response dict to be returned by Lambda
    when using Bedrock Agent Functions.

    Since the payload format is different from the standard API Gateway Proxy event,
    we override the build method.
    """

    @override
    def build(self, event: BedrockAgentFunctionEvent, *args) -> dict[str, Any]:
        """Build the full response dict to be returned by the lambda"""
        self._route(event, None)

        body = self.response.body
        if self.response.is_json() and not isinstance(self.response.body, str):
            body = self.serializer(body)

        response: dict[str, Any] = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.action_group,
                "function": event.function,
                "functionResponse": {"responseBody": {"TEXT": {"body": str(body)}}},
            },
        }

        # Add responseState if it's an error
        if self.response.status_code >= 400:
            response["response"]["functionResponse"]["responseState"] = (
                ResponseState.REPROMPT.value if self.response.status_code == 400 else ResponseState.FAILURE.value
            )

        return response


class BedrockAgentFunctionResolver:
    """Bedrock Agent Function resolver that handles function definitions

    Examples
    --------
    ```python
    from aws_lambda_powertools.event_handler import BedrockAgentFunctionResolver

    app = BedrockAgentFunctionResolver()

    @app.tool(description="Gets the current UTC time")
    def get_current_time():
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self.current_event: BedrockAgentFunctionEvent | None = None
        self._response_builder_class = BedrockFunctionsResponseBuilder

    def tool(
        self,
        description: str | None = None,
        name: str | None = None,
    ) -> Callable:
        """Decorator to register a tool function

        Parameters
        ----------
        description : str | None
            Description of what the tool does
        name : str | None
            Custom name for the tool. If not provided, uses the function name
        """

        def decorator(func: Callable) -> Callable:
            if not description:
                raise ValueError("Tool description is required")

            function_name = name or func.__name__
            if function_name in self._tools:
                raise ValueError(f"Tool '{function_name}' already registered")

            self._tools[function_name] = {
                "function": func,
                "description": description,
            }
            return func

        return decorator

    def resolve(self, event: dict[str, Any], context: Any) -> dict[str, Any]:
        """Resolves the function call from Bedrock Agent event"""
        try:
            self.current_event = BedrockAgentFunctionEvent(event)
            return self._resolve()
        except KeyError as e:
            raise ValueError(f"Missing required field: {str(e)}")

    def _resolve(self) -> dict[str, Any]:
        """Internal resolution logic"""
        if self.current_event is None:
            raise ValueError("No event to process")

        function_name = self.current_event.function

        if function_name not in self._tools:
            return self._response_builder_class(
                Response(
                    status_code=400,  # Using 400 to trigger REPROMPT
                    body=f"Function not found: {function_name}",
                ),
            ).build(self.current_event)

        try:
            result = self._tools[function_name]["function"]()
            # Always wrap the result in a Response object
            if not isinstance(result, Response):
                result = Response(
                    status_code=200,  # Success
                    body=result,
                )
            return self._response_builder_class(result).build(self.current_event)
        except Exception as e:
            return self._response_builder_class(
                Response(
                    status_code=500,  # Using 500 to trigger FAILURE
                    body=f"Error: {str(e)}",
                ),
            ).build(self.current_event)

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent


class BedrockAgentFunctionResolver:
    """Bedrock Agent Function resolver that handles function definitions

    Examples
    --------
    Simple example with a custom lambda handler

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

    def tool(self, description: str | None = None) -> Callable:
        """Decorator to register a tool function"""

        def decorator(func: Callable) -> Callable:
            if not description:
                raise ValueError("Tool description is required")

            function_name = func.__name__
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
        action_group = self.current_event.action_group

        if function_name not in self._tools:
            return self._create_response(
                action_group=action_group,
                function_name=function_name,
                result=f"Function not found: {function_name}",
            )

        try:
            result = self._tools[function_name]["function"]()
            return self._create_response(action_group=action_group, function_name=function_name, result=result)
        except Exception as e:
            return self._create_response(
                action_group=action_group,
                function_name=function_name,
                result=f"Error: {str(e)}",
            )

    def _create_response(self, action_group: str, function_name: str, result: Any) -> dict[str, Any]:
        """Create response in Bedrock Agent format"""
        return {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": action_group,
                "function": function_name,
                "functionResponse": {"responseBody": {"TEXT": {"body": str(result)}}},
            },
        }

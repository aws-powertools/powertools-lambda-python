from __future__ import annotations

import inspect
import warnings
from typing import TYPE_CHECKING, Any, Literal

from aws_lambda_powertools.warnings import PowertoolsUserWarning

if TYPE_CHECKING:
    from collections.abc import Callable

from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent


class BedrockFunctionResponse:
    """Response class for Bedrock Agent Functions

    Parameters
    ----------
    body : Any, optional
        Response body
    session_attributes : dict[str, str] | None
        Session attributes to include in the response
    prompt_session_attributes : dict[str, str] | None
        Prompt session attributes to include in the response
    response_state : Literal["FAILURE", "REPROMPT"] | None
        Response state ("FAILURE" or "REPROMPT")

    Examples
    --------
    ```python
    @app.tool(description="Function that uses session attributes")
    def test_function():
        return BedrockFunctionResponse(
            body="Hello",
            session_attributes={"userId": "123"},
            prompt_session_attributes={"lastAction": "login"}
        )
    ```
    """

    def __init__(
        self,
        body: Any = None,
        session_attributes: dict[str, str] | None = None,
        prompt_session_attributes: dict[str, str] | None = None,
        knowledge_bases: list[dict[str, Any]] | None = None,
        response_state: Literal["FAILURE", "REPROMPT"] | None = None,
    ) -> None:
        if response_state is not None and response_state not in ["FAILURE", "REPROMPT"]:
            raise ValueError("responseState must be 'FAILURE' or 'REPROMPT'")

        self.body = body
        self.session_attributes = session_attributes
        self.prompt_session_attributes = prompt_session_attributes
        self.knowledge_bases = knowledge_bases
        self.response_state = response_state


class BedrockFunctionsResponseBuilder:
    """
    Bedrock Functions Response Builder. This builds the response dict to be returned by Lambda
    when using Bedrock Agent Functions.
    """

    def __init__(self, result: BedrockFunctionResponse | Any) -> None:
        self.result = result

    def build(self, event: BedrockAgentFunctionEvent) -> dict[str, Any]:
        """Build the full response dict to be returned by the lambda"""
        if isinstance(self.result, BedrockFunctionResponse):
            body = self.result.body
            session_attributes = self.result.session_attributes
            prompt_session_attributes = self.result.prompt_session_attributes
            knowledge_bases = self.result.knowledge_bases
            response_state = self.result.response_state

        else:
            body = self.result
            session_attributes = None
            prompt_session_attributes = None
            knowledge_bases = None
            response_state = None

        # Per AWS Bedrock documentation, currently only "TEXT" is supported as the responseBody content type
        # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        response: dict[str, Any] = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.action_group,
                "function": event.function,
                "functionResponse": {"responseBody": {"TEXT": {"body": str(body if body is not None else "")}}},
            },
        }

        # Add responseState if provided
        if response_state:
            response["response"]["functionResponse"]["responseState"] = response_state

        # Add session attributes if provided in response or maintain from input
        response.update(
            {
                "sessionAttributes": session_attributes or event.session_attributes or {},
                "promptSessionAttributes": prompt_session_attributes or event.prompt_session_attributes or {},
            },
        )

        # Add knowledge bases configuration if provided
        if knowledge_bases:
            response["knowledgeBasesConfiguration"] = knowledge_bases

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
            function_name = name or func.__name__
            if function_name in self._tools:
                warnings.warn(
                    f"Tool '{function_name}' already registered. Overwriting with new definition.",
                    PowertoolsUserWarning,
                    stacklevel=2,
                )

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

        try:
            parameters = {}
            if hasattr(self.current_event, "parameters"):
                for param in self.current_event.parameters:
                    parameters[param.name] = param.value

            func = self._tools[function_name]["function"]
            sig = inspect.signature(func)

            valid_params = {}
            for name, value in parameters.items():
                if name in sig.parameters:
                    valid_params[name] = value

            result = func(**valid_params)
            return BedrockFunctionsResponseBuilder(result).build(self.current_event)
        except Exception as e:
            return BedrockFunctionsResponseBuilder(
                BedrockFunctionResponse(
                    body=f"Error: {str(e)}",
                ),
            ).build(self.current_event)

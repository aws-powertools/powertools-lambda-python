from __future__ import annotations

import inspect
import json
import logging
import warnings
from collections.abc import Callable
from typing import Any, Literal, TypeVar

from aws_lambda_powertools.utilities.data_classes import BedrockAgentFunctionEvent
from aws_lambda_powertools.warnings import PowertoolsUserWarning

# Define a generic type for the function
T = TypeVar("T", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class BedrockFunctionResponse:
    """Response class for Bedrock Agent Functions.

    Parameters
    ----------
    body : Any, optional
        Response body to be returned to the caller.
    session_attributes : dict[str, str] or None, optional
        Session attributes to include in the response for maintaining state.
    prompt_session_attributes : dict[str, str] or None, optional
        Prompt session attributes to include in the response.
    knowledge_bases : list[dict[str, Any]] or None, optional
        Knowledge bases to include in the response.
    response_state : {"FAILURE", "REPROMPT"} or None, optional
        Response state indicating if the function failed or needs reprompting.

    Examples
    --------
    >>> @app.tool(description="Function that uses session attributes")
    >>> def test_function():
    ...     return BedrockFunctionResponse(
    ...         body="Hello",
    ...         session_attributes={"userId": "123"},
    ...         prompt_session_attributes={"lastAction": "login"}
    ...     )

    Notes
    -----
    The `response_state` parameter can only be set to "FAILURE" or "REPROMPT".
    """

    def __init__(
        self,
        body: Any = None,
        session_attributes: dict[str, str] | None = None,
        prompt_session_attributes: dict[str, str] | None = None,
        knowledge_bases: list[dict[str, Any]] | None = None,
        response_state: Literal["FAILURE", "REPROMPT"] | None = None,
    ) -> None:
        if response_state and response_state not in ["FAILURE", "REPROMPT"]:
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

    def build(self, event: BedrockAgentFunctionEvent, serializer: Callable) -> dict[str, Any]:
        result_obj = self.result

        # Extract attributes from BedrockFunctionResponse or use defaults
        body = getattr(result_obj, "body", result_obj)
        session_attributes = getattr(result_obj, "session_attributes", None)
        prompt_session_attributes = getattr(result_obj, "prompt_session_attributes", None)
        knowledge_bases = getattr(result_obj, "knowledge_bases", None)
        response_state = getattr(result_obj, "response_state", None)

        # Build base response structure
        # Per AWS Bedrock documentation, currently only "TEXT" is supported as the responseBody content type
        # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        response: dict[str, Any] = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": event.action_group,
                "function": event.function,
                "functionResponse": {
                    "responseBody": {"TEXT": {"body": serializer(body if body is not None else "")}},
                },
            },
            "sessionAttributes": session_attributes or event.session_attributes or {},
            "promptSessionAttributes": prompt_session_attributes or event.prompt_session_attributes or {},
        }

        # Add optional fields when present
        if response_state:
            response["response"]["functionResponse"]["responseState"] = response_state

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

    @app.tool(name="get_current_time", description="Gets the current UTC time")
    def get_current_time():
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def lambda_handler(event, context):
        return app.resolve(event, context)
    ```
    """

    context: dict

    def __init__(self, serializer: Callable | None = None) -> None:
        self._tools: dict[str, dict[str, Any]] = {}
        self.current_event: BedrockAgentFunctionEvent | None = None
        self.context = {}
        self._response_builder_class = BedrockFunctionsResponseBuilder
        self.serializer = serializer or json.dumps

    def tool(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> Callable[[T], T]:
        """Decorator to register a tool function

        Parameters
        ----------
        name : str | None
            Custom name for the tool. If not provided, uses the function name
        description : str | None
            Description of what the tool does

        Returns
        -------
        Callable
            Decorator function that registers and returns the original function
        """

        def decorator(func: T) -> T:
            function_name = name or func.__name__

            logger.debug(f"Registering {function_name} tool")

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
            raise ValueError(f"Missing required field: {str(e)}") from e

    def _resolve(self) -> dict[str, Any]:
        """Internal resolution logic"""
        if self.current_event is None:
            raise ValueError("No event to process")

        function_name = self.current_event.function

        logger.debug(f"Resolving {function_name} tool")

        try:
            parameters: dict[str, Any] = {}
            # Extract parameters from the event
            for param in getattr(self.current_event, "parameters", []):
                param_type = getattr(param, "type", None)
                if param_type == "string":
                    parameters[param.name] = str(param.value)
                elif param_type == "integer":
                    try:
                        parameters[param.name] = int(param.value)
                    except (ValueError, TypeError):
                        parameters[param.name] = param.value
                elif param_type == "number":
                    try:
                        parameters[param.name] = float(param.value)
                    except (ValueError, TypeError):
                        parameters[param.name] = param.value
                elif param_type == "boolean":
                    if isinstance(param.value, str):
                        parameters[param.name] = param.value.lower() == "true"
                    else:
                        parameters[param.name] = bool(param.value)
                else:  # "array" or any other type
                    parameters[param.name] = param.value

            func = self._tools[function_name]["function"]
            # Filter parameters to only include those expected by the function
            sig = inspect.signature(func)
            valid_params = {name: value for name, value in parameters.items() if name in sig.parameters}

            # Call the function with the filtered parameters
            result = func(**valid_params)

            self.clear_context()

            # Build and return the response
            return BedrockFunctionsResponseBuilder(result).build(self.current_event, serializer=self.serializer)
        except Exception as error:
            # Return a formatted error response
            logger.error(f"Error processing function: {function_name}", exc_info=True)
            error_response = BedrockFunctionResponse(body=f"Error: {error.__class__.__name__}: {str(error)}")
            return BedrockFunctionsResponseBuilder(error_response).build(self.current_event, serializer=self.serializer)

    def append_context(self, **additional_context):
        """Append key=value data as routing context"""
        self.context.update(**additional_context)

    def clear_context(self):
        """Resets routing context"""
        self.context.clear()

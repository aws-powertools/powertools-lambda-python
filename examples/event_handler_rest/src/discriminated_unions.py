from typing import Literal, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Body
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)


class FooAction(BaseModel):
    """Action type for foo operations."""

    action: Literal["foo"] = "foo"
    foo_data: str


class BarAction(BaseModel):
    """Action type for bar operations."""

    action: Literal["bar"] = "bar"
    bar_data: int


ActionType = Annotated[Union[FooAction, BarAction], Field(discriminator="action")]  # (1)!


@app.post("/actions")
@tracer.capture_method
def handle_action(action: Annotated[ActionType, Body(description="Action to perform")]):  # (2)!
    """Handle different action types using discriminated unions."""
    if isinstance(action, FooAction):
        return {"message": f"Handling foo action with data: {action.foo_data}"}
    elif isinstance(action, BarAction):
        return {"message": f"Handling bar action with data: {action.bar_data}"}


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

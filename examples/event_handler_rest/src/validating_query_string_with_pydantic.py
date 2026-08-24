from typing import Any, Dict

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver(enable_validation=True)


class Todo(BaseModel):
    userId: int
    id_: int | None = Field(alias="id", default=None)
    title: str
    completed: bool


@app.get("/todos")
@tracer.capture_method
def get_todos(todo: Annotated[Todo, Query()]) -> Dict[str, Any]:  # (1)!
    return todo.model_dump()


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_HTTP)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

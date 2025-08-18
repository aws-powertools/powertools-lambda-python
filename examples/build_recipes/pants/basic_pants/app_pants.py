from __future__ import annotations

from typing import Any

import requests
from pydantic import BaseModel

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()
metrics = Metrics()
app = APIGatewayRestResolver()


class TodoItem(BaseModel):
    id: int
    title: str
    completed: bool = False
    user_id: int | None = None


@app.get("/todos")
@tracer.capture_method
def get_todos() -> TodoItem:
    """Fetch todos from external API"""
    logger.info("Fetching todos from external API")

    response = requests.get("https://jsonplaceholder.typicode.com/todos")
    response.raise_for_status()

    return response.json()[0]


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def lambda_handler(event: dict[str, Any], context: LambdaContext):
    return app.resolve(event, context)

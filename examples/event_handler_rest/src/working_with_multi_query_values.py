from __future__ import annotations

from enum import Enum

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Query
from aws_lambda_powertools.shared.types import Annotated
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)


class ExampleEnum(Enum):
    """Example of an Enum class."""

    ONE = "value_one"
    TWO = "value_two"
    THREE = "value_three"


@app.get("/todos")
def get(
    example_multi_value_param: Annotated[
        list[ExampleEnum],  # (1)!
        Query(
            description="This is multi value query parameter.",
        ),
    ],
):
    """Return validated multi-value param values."""
    return example_multi_value_param


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

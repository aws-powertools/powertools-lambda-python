from enum import Enum
from typing import List

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.openapi.params import Header
from aws_lambda_powertools.shared.types import Annotated
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)


class CountriesAllowed(Enum):
    """Example of an Enum class."""

    US = "US"
    PT = "PT"
    BR = "BR"


@app.get("/hello")
def get(
    cloudfront_viewer_country: Annotated[
        List[CountriesAllowed],  # (1)!
        Header(
            description="This is multi value header parameter.",
        ),
    ],
):
    """Return validated multi-value header values."""
    return cloudfront_viewer_country


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

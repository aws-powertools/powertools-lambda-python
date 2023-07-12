import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils
from aws_lambda_powertools.utilities.typing import LambdaContext

app = AppSyncResolver()
tracer = Tracer()
logger = Logger()


class Merchant(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    name: str
    description: str
    commonField: str


@app.resolver(type_name="Query", field_name="findMerchant")
def find_merchant(search: str) -> List[Merchant]:
    merchants: List[Merchant] = [
        {
            "id": scalar_types_utils.make_id(),
            "name": "Parry-Wood",
            "description": "Possimus doloremque tempora harum deleniti eum.",
        },
        {
            "id": scalar_types_utils.make_id(),
            "name": "Shaw, Owen and Jones",
            "description": "Aliquam iste architecto suscipit in.",
        },
    ]

    return [merchant for merchant in merchants if search == merchant["name"]]


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

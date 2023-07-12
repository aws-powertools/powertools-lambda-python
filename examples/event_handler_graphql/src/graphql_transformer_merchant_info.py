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

tracer = Tracer()
logger = Logger()
app = AppSyncResolver()


class Location(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    name: str
    description: str
    address: str
    commonField: str


@app.resolver(type_name="Query", field_name="listLocations")
def list_locations(page: int = 0, size: int = 10) -> List[Location]:
    return [{"id": scalar_types_utils.make_id(), "name": "Smooth Grooves"}]


@app.resolver(field_name="commonField")
def common_field() -> str:
    # Would match all fieldNames matching 'commonField'
    return scalar_types_utils.make_id()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.APPSYNC_RESOLVER)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

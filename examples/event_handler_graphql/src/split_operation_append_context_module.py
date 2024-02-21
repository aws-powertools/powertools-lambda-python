from typing import List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.graphql_appsync.router import Router
from aws_lambda_powertools.shared.types import TypedDict

tracer = Tracer()
logger = Logger()
router = Router()


class Location(TypedDict, total=False):
    id: str  # noqa AA03 VNE003, required due to GraphQL Schema
    name: str
    description: str
    address: str


@router.resolver(field_name="listLocations")
@router.resolver(field_name="locations")
@tracer.capture_method
def get_locations(name: str, description: str = "") -> List[Location]:  # match GraphQL Query arguments
    is_admin: bool = router._router_context.context.get("is_admin", False)
    return [{"name": name, "description": description}] if is_admin else []

from typing import Any, Dict, List

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.appsync import Router

logger = Logger(child=True)
router = Router()


@router.resolver(type_name="Query", field_name="listLocations")
def list_locations(merchant_id: str) -> List[Dict[str, Any]]:
    return [{"name": "Location name", "merchant_id": merchant_id}]


@router.resolver(type_name="Location", field_name="status")
def resolve_status(merchant_id: str) -> str:
    logger.debug(f"Resolve status for merchant_id: {merchant_id}")
    return "FOO"

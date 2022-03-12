from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

router = Router()
logger = Logger(child=True)


@router.get("/status")
def health() -> Dict:
    logger.debug("Health check called")
    return {"status": "OK"}

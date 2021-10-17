from typing import Dict

from aws_lambda_powertools.event_handler.api_gateway import Router

router = Router()


@router.get("/status")
def health() -> Dict:
    return {"status": "OK"}

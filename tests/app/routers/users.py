from typing import Dict

from aws_lambda_powertools.event_handler.api_gateway import Router

router = Router()


@router.get("/users/<name>")
def find_users_by_name(name: str) -> Dict:
    return {"users": [{"name": name}]}

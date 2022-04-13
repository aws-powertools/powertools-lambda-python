from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(child=True)
router = Router()
USERS = {"user1": "details", "user2": "details", "user3": "details"}


@router.get("/")  # /users, when we set the prefix in app.py
def get_users() -> Dict:
    ...


@router.get("/<username>")
def get_user(username: str) -> Dict:
    ...


# many other related /users routing

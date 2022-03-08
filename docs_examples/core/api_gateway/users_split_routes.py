import itertools
from typing import Dict

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import Router

logger = Logger(child=True)
router = Router()
USERS = {"user1": "details_here", "user2": "details_here", "user3": "details_here"}


@router.get("/users")
def get_users() -> Dict:
    # /users?limit=1
    pagination_limit = router.current_event.get_query_string_value(name="limit", default_value=10)

    logger.info(f"Fetching the first {pagination_limit} users...")
    ret = dict(itertools.islice(USERS.items(), int(pagination_limit)))
    return {"items": [ret]}


@router.get("/users/<username>")
def get_user(username: str) -> Dict:
    logger.info(f"Fetching username {username}")
    return {"details": USERS.get(username, {})}


# many other related /users routing

import json
from dataclasses import dataclass
from http import HTTPStatus

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# This would likely be a db lookup
users = [
    {
        "user_id": "b0b2a5bf-ee1e-4c5e-9a86-91074052739e",
        "email": "john.doe@example.com",
        "active": True,
    },
    {
        "user_id": "3a9df6b1-938c-4e80-bd4a-0c966f4b1c1e",
        "email": "jane.smith@example.com",
        "active": False,
    },
    {
        "user_id": "aa0d3d09-9cb9-42b9-9e63-1fb17ea52981",
        "email": "alex.wilson@example.com",
        "active": True,
    },
]


@dataclass
class User:
    user_id: str
    email: str
    active: bool


def get_user_by_id(user_id: str) -> Union[User, None]:
    for user_data in users:
        if user_data["user_id"] == user_id:
            return User(
                user_id=str(user_data["user_id"]),
                email=str(user_data["email"]),
                active=bool(user_data["active"]),
            )
            
    return None


app = APIGatewayRestResolver()


@app.get("/users/<user_id>")
def all_active_users(user_id: str):
    """HTTP Response for all active users"""
    user = get_user_by_id(user_id)

    if user:
        return Response(
            status_code=HTTPStatus.OK.value,
            content_type="application/json",
            body=json.dumps(user.__dict__),
        )

    else:
        return Response(status_code=HTTPStatus.NOT_FOUND)


@logger.inject_lambda_context()
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

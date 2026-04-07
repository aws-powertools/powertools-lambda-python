from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError
from aws_lambda_powertools.event_handler.request import Request
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()


def get_authenticated_user(request: Request) -> str:
    user_id = request.headers.get("x-user-id")
    if not user_id:
        raise UnauthorizedError("Missing authentication")
    return user_id


@app.get("/profile")
def get_profile(user_id: Annotated[str, Depends(get_authenticated_user)]):
    return {"user_id": user_id}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

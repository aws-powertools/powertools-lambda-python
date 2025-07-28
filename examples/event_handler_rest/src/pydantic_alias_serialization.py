from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_snake

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)


class UserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_snake, populate_by_name=True)  # (1)!

    firstName: str  # Will be serialized as "first_name"
    lastName: str  # Will be serialized as "last_name"


@app.get("/user")
def get_user() -> UserResponse:
    return UserResponse(firstName="John", lastName="Doe")  # (2)!
    # Response will be: {"first_name": "John", "last_name": "Doe"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

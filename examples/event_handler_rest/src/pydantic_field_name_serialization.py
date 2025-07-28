from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_snake

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver(enable_validation=True)


class UserResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_snake, populate_by_name=True)

    firstName: str
    lastName: str


@app.get("/user")
def get_user_manual() -> dict:
    user = UserResponse(firstName="John", lastName="Doe")
    return user.model_dump(by_alias=False)  # Returns dict, not UserResponse


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)

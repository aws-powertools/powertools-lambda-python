from pydantic import BaseModel, model_validator

from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.typing import LambdaContext


class UserModel(BaseModel):
    username: str
    parentid_1: str
    parentid_2: str

    @model_validator(mode="after")  # (1)!
    def check_parents_match(cls, values):
        pi1, pi2 = values.get("parentid_1"), values.get("parentid_2")
        if pi1 is not None and pi2 is not None and pi1 != pi2:
            raise ValueError("Parent ids do not match")
        return values


def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=UserModel, event=event)
        return {
            "statusCode": 200,
            "body": f"Received parent id from: {parsed_event.username}",
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": str(e),
        }

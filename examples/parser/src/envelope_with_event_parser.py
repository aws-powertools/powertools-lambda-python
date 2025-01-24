from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import envelopes, event_parser
from aws_lambda_powertools.utilities.typing import LambdaContext


class UserModel(BaseModel):
    username: str
    parentid_1: str
    parentid_2: str


@event_parser(model=UserModel, envelope=envelopes.EventBridgeEnvelope)
def lambda_handler(event: UserModel, context: LambdaContext):
    if event.parentid_1 != event.parentid_2:
        return {"statusCode": 400, "body": "Parent ids do not match"}

    # If parentids match, proceed with user registration

    return {"statusCode": 200, "body": f"User {event.username} registered successfully"}

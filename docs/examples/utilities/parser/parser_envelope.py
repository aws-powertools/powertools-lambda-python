from aws_lambda_powertools.utilities.parser import BaseModel, envelopes, event_parser, parse
from aws_lambda_powertools.utilities.typing import LambdaContext


class UserModel(BaseModel):
    username: str
    password1: str
    password2: str


payload = {
    "version": "0",
    "id": "6a7e8feb-b491-4cf7-a9f1-bf3703467718",
    "detail-type": "CustomerSignedUp",
    "source": "CustomerService",
    "account": "111122223333",
    "time": "2020-10-22T18:43:48Z",
    "region": "us-west-1",
    "resources": ["some_additional_"],
    "detail": {
        "username": "universe",
        "password1": "myp@ssword",
        "password2": "repeat password",
    },
}

ret = parse(model=UserModel, envelope=envelopes.EventBridgeEnvelope, event=payload)

# Parsed model only contains our actual model, not the entire EventBridge + Payload parsed
assert ret.password1 == ret.password2

# Same behaviour but using our decorator
@event_parser(model=UserModel, envelope=envelopes.EventBridgeEnvelope)
def handler(event: UserModel, context: LambdaContext):
    assert event.password1 == event.password2

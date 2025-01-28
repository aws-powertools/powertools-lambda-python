from aws_lambda_powertools.utilities.parser import BaseModel, field_validator, parse
from aws_lambda_powertools.utilities.typing import LambdaContext


class HelloWorldModel(BaseModel):
    message: str
    sender: str

    @field_validator("*")
    def has_whitespace(cls, v):
        if " " not in v:
            raise ValueError("Must have whitespace...")
        return v


def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=HelloWorldModel, event=event)
        return {
            "statusCode": 200,
            "body": f"Received message: {parsed_event.message}",
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": str(e),
        }

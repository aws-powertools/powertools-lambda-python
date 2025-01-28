from pydantic import BaseModel, field_validator

from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.typing import LambdaContext


class HelloWorldModel(BaseModel):
    message: str

    @field_validator("message")
    def is_hello_world(cls, v):
        if v != "hello world":
            raise ValueError("Message must be hello world!")
        return v


def lambda_handler(event: dict, context: LambdaContext):
    try:
        parsed_event = parse(model=HelloWorldModel, event=event)
        return {"statusCode": 200, "body": f"Received message: {parsed_event.message}"}
    except ValueError as e:
        return {"statusCode": 400, "body": str(e)}

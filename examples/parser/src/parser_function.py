from pydantic import BaseModel, ValidationError

from aws_lambda_powertools.utilities.parser import parse


# Define a Pydantic model for the expected structure of the input
class MyEvent(BaseModel):
    id: int
    name: str


def lambda_handler(event: dict, context):
    try:
        # Manually parse the incoming event into MyEvent model
        parsed_event: MyEvent = parse(model=MyEvent, event=event)
        return {"statusCode": 200, "body": f"Hello {parsed_event.name}, your ID is {parsed_event.id}"}
    except ValidationError as e:
        # Catch validation errors and return a 400 response
        return {"statusCode": 400, "body": f"Validation error: {str(e)}"}

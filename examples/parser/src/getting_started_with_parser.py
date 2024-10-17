from aws_lambda_powertools.utilities.parser import BaseModel, event_parser, ValidationError

class MyEvent(BaseModel):
    id: int
    name: str

@event_parser(model=MyEvent)
def lambda_handler(event: MyEvent, context):
    try:
        return {"statusCode": 200, "body": f"Hello {event.name}, your ID is {event.id}"}
    except ValidationError as e:
        return {"statusCode": 400, "body": f"Invalid input: {str(e)}"}
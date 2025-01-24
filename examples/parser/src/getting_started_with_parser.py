from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import event_parser


class MyEvent(BaseModel):
    id: int
    name: str


@event_parser(model=MyEvent)
def lambda_handler(event: MyEvent, context):
    # if your model is valid, you can return
    return {"statusCode": 200, "body": f"Hello {event.name}, your ID is {event.id}"}

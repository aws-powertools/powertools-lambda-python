from pydantic import Field, ValidationError

from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel


# Define a custom EventBridge model by extending the built-in EventBridgeModel
class MyCustomEventBridgeModel(EventBridgeModel):  # type: ignore[override]
    detail_type: str = Field(alias="detail-type")
    source: str
    detail: dict


def lambda_handler(event: dict, context):
    try:
        # Manually parse the incoming event into the custom model
        parsed_event: MyCustomEventBridgeModel = parse(model=MyCustomEventBridgeModel, event=event)

        return {"statusCode": 200, "body": f"Event from {parsed_event.source}, type: {parsed_event.detail_type}"}
    except ValidationError as e:
        return {"statusCode": 400, "body": f"Validation error: {str(e)}"}

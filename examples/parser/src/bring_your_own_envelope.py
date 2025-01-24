import json
from typing import Any, Dict, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import BaseEnvelope, event_parser
from aws_lambda_powertools.utilities.parser.models import EventBridgeModel
from aws_lambda_powertools.utilities.typing import LambdaContext

Model = TypeVar("Model", bound=BaseModel)


class EventBridgeEnvelope(BaseEnvelope):
    def parse(self, data: Optional[Union[Dict[str, Any], Any]], model: Type[Model]) -> Optional[Model]:
        if data is None:
            return None

        parsed_envelope = EventBridgeModel.model_validate(data)
        return self._parse(data=parsed_envelope.detail, model=model)


class OrderDetail(BaseModel):
    order_id: str
    amount: float
    customer_id: str


@event_parser(model=OrderDetail, envelope=EventBridgeEnvelope)
def lambda_handler(event: OrderDetail, context: LambdaContext):
    try:
        # Process the order
        print(f"Processing order {event.order_id} for customer {event.customer_id}")
        print(f"Order amount: ${event.amount:.2f}")

        # Your business logic here
        # For example, you might save the order to a database or trigger a payment process

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Order {event.order_id} processed successfully",
                    "order_id": event.order_id,
                    "amount": event.amount,
                    "customer_id": event.customer_id,
                },
            ),
        }
    except Exception as e:
        print(f"Error processing order: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Internal server error"})}

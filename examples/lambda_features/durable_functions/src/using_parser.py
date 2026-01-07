from aws_durable_execution_sdk_python import DurableContext, durable_execution  # type: ignore[import-not-found]
from pydantic import BaseModel

from aws_lambda_powertools.utilities.parser import event_parser


class OrderEvent(BaseModel):
    order_id: str
    amount: float


@event_parser(model=OrderEvent)
@durable_execution
def handler(event: OrderEvent, context: DurableContext) -> str:
    # Event is already validated and parsed
    context.logger.info("Processing order", extra={"order_id": event.order_id})

    result: str = context.step(
        lambda _: f"processed-{event.order_id}",
        name="process_order",
    )

    return result

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.typing import LambdaContext

dynamodb = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(event_key_jmespath="order_id")  # see Choosing a payload subset section


class OrderItem(BaseModel):
    sku: str
    description: str


class Order(BaseModel):
    item: OrderItem
    order_id: int


@idempotent_function(data_keyword_argument="order", config=config, persistence_store=dynamodb)
def process_order(order: Order):
    return f"processed order {order.order_id}"


def lambda_handler(event: dict, context: LambdaContext):
    config.register_lambda_context(context)  # see Lambda timeouts section
    order_item = OrderItem(sku="fake", description="sample")
    order = Order(item=order_item, order_id=1)

    # `order` parameter must be called as a keyword argument to work
    process_order(order=order)

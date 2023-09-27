from typing import Dict, Type

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.serialization.custom_dict import CustomDictSerializer
from aws_lambda_powertools.utilities.typing import LambdaContext

dynamodb = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(event_key_jmespath="order_id")  # see Choosing a payload subset section


class OrderItem:
    def __init__(self, sku: str, description: str):
        self.sku = sku
        self.description = description


class Order:
    def __init__(self, item: OrderItem, order_id: int):
        self.item = item
        self.order_id = order_id


class OrderOutput:
    def __init__(self, order_id: int):
        self.order_id = order_id


def order_to_dict(x: Type[OrderOutput]) -> Dict:  # (1)!
    return x.__dict__


def dict_to_order(x: Dict) -> OrderOutput:  # (2)!
    return OrderOutput(**x)


order_output_serializer = CustomDictSerializer(  # (3)!
    to_dict=order_to_dict,
    from_dict=dict_to_order,
)


@idempotent_function(
    data_keyword_argument="order",
    config=config,
    persistence_store=dynamodb,
    output_serializer=order_output_serializer,
)
def process_order(order: Order) -> OrderOutput:
    return OrderOutput(order_id=order.order_id)


def lambda_handler(event: dict, context: LambdaContext):
    config.register_lambda_context(context)  # see Lambda timeouts section
    order_item = OrderItem(sku="fake", description="sample")
    order = Order(item=order_item, order_id=1)

    # `order` parameter must be called as a keyword argument to work
    process_order(order=order)

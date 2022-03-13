from dataclasses import dataclass

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent_function

dynamodb = DynamoDBPersistenceLayer(table_name="idem")
config = IdempotencyConfig(
    event_key_jmespath="order_id",  # see Choosing a payload subset section
    use_local_cache=True,
)


@dataclass
class OrderItem:
    sku: str
    description: str


@dataclass
class Order:
    item: OrderItem
    order_id: int


@idempotent_function(data_keyword_argument="order", config=config, persistence_store=dynamodb)
def process_order(order: Order):
    return f"processed order {order.order_id}"


order_item = OrderItem(sku="fake", description="sample")
order = Order(item=order_item, order_id="fake-id")

# `order` parameter must be called as a keyword argument to work
process_order(order=order)

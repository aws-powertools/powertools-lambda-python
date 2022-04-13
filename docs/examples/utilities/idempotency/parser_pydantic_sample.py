from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent_function
from aws_lambda_powertools.utilities.parser import BaseModel

dynamodb = DynamoDBPersistenceLayer(table_name="idem")
config = IdempotencyConfig(
    event_key_jmespath="order_id",  # see Choosing a payload subset section
    use_local_cache=True,
)


class OrderItem(BaseModel):
    sku: str
    description: str


class Order(BaseModel):
    item: OrderItem
    order_id: int


@idempotent_function(data_keyword_argument="order", config=config, persistence_store=dynamodb)
def process_order(order: Order):
    return f"processed order {order.order_id}"


order_item = OrderItem(sku="fake", description="sample")
order = Order(item=order_item, order_id="fake-id")

# `order` parameter must be called as a keyword argument to work
process_order(order=order)

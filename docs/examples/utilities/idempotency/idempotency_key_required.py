from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

# Requires "user"."uid" and "order_id" to be present
config = IdempotencyConfig(
    event_key_jmespath="[user.uid, order_id]",
    raise_on_no_idempotency_key=True,
)


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    ...

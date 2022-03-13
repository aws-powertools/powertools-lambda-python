from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

persistence_layer = DynamoDBPersistenceLayer(
    table_name="IdempotencyTable",
    sort_key_attr="sort_key",
)


@idempotent(persistence_store=persistence_layer)
def handler(event, context):
    return {"message": "success", "id": event["body"]["id"]}

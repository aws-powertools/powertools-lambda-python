from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {
        "message": "success",
        "statusCode": 200,
    }

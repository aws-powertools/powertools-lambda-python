from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="idempotency")


@idempotent(persistence_store=persistence_layer)
def handler(event, context):
    print("expensive operation")
    return {
        "payment_id": 12345,
        "message": "success",
        "statusCode": 200,
    }

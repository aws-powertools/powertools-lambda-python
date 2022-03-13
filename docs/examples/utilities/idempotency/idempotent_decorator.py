from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(persistence_store=persistence_layer)
def handler(event, context):
    payment = create_subscription_payment(user=event["user"], product=event["product_id"])
    ...
    return {
        "payment_id": payment.id,
        "message": "success",
        "statusCode": 200,
    }

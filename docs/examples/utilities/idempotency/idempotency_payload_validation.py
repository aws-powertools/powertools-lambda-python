from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

config = IdempotencyConfig(
    event_key_jmespath="[userDetail, productId]",
    payload_validation_jmespath="amount",
)
persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    # Creating a subscription payment is a side
    # effect of calling this function!
    payment = create_subscription_payment(
        user=event["userDetail"]["username"],
        product=event["product_id"],
        amount=event["amount"],
    )
    ...
    return {
        "message": "success",
        "statusCode": 200,
        "payment_id": payment.id,
        "amount": payment.amount,
    }

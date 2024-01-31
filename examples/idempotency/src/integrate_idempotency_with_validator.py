from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.validation import envelopes, validator

config = IdempotencyConfig(event_key_jmespath='["message", "username"]')
persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")


@validator(envelope=envelopes.API_GATEWAY_HTTP)
@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context: LambdaContext):
    return {"message": event["message"], "statusCode": 200}

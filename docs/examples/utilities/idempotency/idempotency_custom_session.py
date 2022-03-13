import boto3

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

boto3_session = boto3.session.Session()
persistence_layer = DynamoDBPersistenceLayer(
    table_name="IdempotencyTable",
    boto3_session=boto3_session,
)

config = IdempotencyConfig(event_key_jmespath="body")


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    ...

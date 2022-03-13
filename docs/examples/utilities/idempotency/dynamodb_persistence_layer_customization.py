from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer

persistence_layer = DynamoDBPersistenceLayer(
    table_name="IdempotencyTable",
    key_attr="idempotency_key",
    expiry_attr="expires_at",
    status_attr="current_status",
    data_attr="result_data",
    validation_key_attr="validation_key",
)

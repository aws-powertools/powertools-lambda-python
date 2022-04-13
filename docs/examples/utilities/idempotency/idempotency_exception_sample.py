import requests

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent_function

dynamodb = DynamoDBPersistenceLayer(table_name="idem")
config = IdempotencyConfig(event_key_jmespath="order_id")


def lambda_handler(event, context):
    # If an exception is raised here, no idempotent record will ever get created as the
    # idempotent function does not get called
    do_some_stuff()

    result = call_external_service(data={"user": "user1", "id": 5})

    # This exception will not cause the idempotent record to be deleted, since it
    # happens after the decorated function has been successfully called
    raise Exception


@idempotent_function(data_keyword_argument="data", config=config, persistence_store=dynamodb)
def call_external_service(data: dict, **kwargs):
    result = requests.post("http://example.com", json={"user": data["user"], "transaction_id": data["id"]})
    return result.json()

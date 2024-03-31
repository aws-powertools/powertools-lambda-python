from typing import Dict

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    IdempotentHookData,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


def my_response_hook(response: Dict, idempotent_data: IdempotentHookData) -> Dict:
    # How to add a field to the response
    response["is_idempotent_response"] = True

    # Must return the response here
    return response


persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

config = IdempotencyConfig(event_key_jmespath="body", response_hook=my_response_hook)


@idempotent(persistence_store=persistence_layer, config=config)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event

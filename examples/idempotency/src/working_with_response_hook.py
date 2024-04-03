from datetime import datetime
from typing import Dict

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    DataRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


def my_response_hook(response: Dict, idempotent_data: DataRecord) -> Dict:
    # Return inserted Header data into the Idempotent Response
    response["headers"]["x-idempotent-key"] = idempotent_data.idempotency_key

    # expiry_timestamp could be None so include if set
    if idempotent_data.expiry_timestamp:
        expiry_time = datetime.fromtimestamp(idempotent_data.expiry_timestamp)
        response["headers"]["x-idempotent-expiration"] = expiry_time.isoformat()

    # Must return the response here
    return response


persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

config = IdempotencyConfig(event_key_jmespath="body", response_hook=my_response_hook)


@idempotent(persistence_store=persistence_layer, config=config)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event

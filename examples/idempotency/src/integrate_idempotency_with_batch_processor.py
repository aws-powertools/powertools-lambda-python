import os

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, process_partial_response
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)

table = os.getenv("IDEMPOTENCY_TABLE")
dynamodb = DynamoDBPersistenceLayer(table_name=table)
config = IdempotencyConfig(event_key_jmespath="messageId")


@idempotent_function(data_keyword_argument="record", config=config, persistence_store=dynamodb)
def record_handler(record: SQSRecord):
    return {"message": record.body}


def lambda_handler(event: SQSRecord, context: LambdaContext):
    config.register_lambda_context(context)  # see Lambda timeouts section

    return process_partial_response(
        event=event,
        context=context,
        processor=processor,
        record_handler=record_handler,
    )

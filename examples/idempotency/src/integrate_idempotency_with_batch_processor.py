from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
processor = BatchProcessor(event_type=EventType.SQS)

dynamodb = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(
    event_key_jmespath="messageId",  # see Choosing a payload subset section
)


@idempotent_function(data_keyword_argument="record", config=config, persistence_store=dynamodb)
def record_handler(record: SQSRecord):
    return {"message": record.body}


def lambda_handler(event: SQSRecord, context: LambdaContext):
    config.register_lambda_context(context)  # see Lambda timeouts section

    # with Lambda context registered for Idempotency
    # we can now kick in the Bach processing logic
    batch = event["Records"]
    with processor(records=batch, handler=record_handler):
        # in case you want to access each record processed by your record_handler
        # otherwise ignore the result variable assignment
        processed_messages = processor.process()
        logger.info(processed_messages)

    return processor.response()

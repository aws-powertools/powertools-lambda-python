from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent_function

processor = BatchProcessor(event_type=EventType.SQS)
dynamodb = DynamoDBPersistenceLayer(table_name="idem")
config = IdempotencyConfig(
    event_key_jmespath="messageId",  # see Choosing a payload subset section
    use_local_cache=True,
)


@idempotent_function(data_keyword_argument="record", config=config, persistence_store=dynamodb)
def record_handler(record: SQSRecord):
    return {"message": record["body"]}


@idempotent_function(data_keyword_argument="data", config=config, persistence_store=dynamodb)
def dummy(arg_one, arg_two, data: dict, **kwargs):
    return {"data": data}


@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context):
    # `data` parameter must be called as a keyword argument to work
    dummy("hello", "universe", data="test")
    return processor.response()

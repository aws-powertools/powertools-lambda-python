import json
import uuid
from random import randint
from typing import Any, Awaitable, Callable, Dict

import pytest

from aws_lambda_powertools.utilities.batch import (
    AsyncBatchProcessor,
    BatchProcessor,
    EventType,
    SqsFifoPartialProcessor,
    async_batch_processor,
    async_process_partial_response,
    batch_processor,
    process_partial_response,
)
from aws_lambda_powertools.utilities.batch.exceptions import BatchProcessingError
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from tests.functional.utils import b64_to_str, str_to_b64


@pytest.fixture(scope="module")
def sqs_event_fifo_factory() -> Callable:
    def factory(body: str, message_group_id: str = ""):
        return {
            "messageId": f"{uuid.uuid4()}",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1703675223472",
                "SequenceNumber": "18882884930918384133",
                "MessageGroupId": message_group_id,
                "SenderId": "SenderId",
                "MessageDeduplicationId": "1eea03c3f7e782c7bdc2f2a917f40389314733ff39f5ab16219580c0109ade98",
                "ApproximateFirstReceiveTimestamp": "1703675223484",
            },
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "awsRegion": "us-east-1",
        }

    return factory


@pytest.fixture(scope="module")
def sqs_event_factory() -> Callable:
    def factory(body: str):
        return {
            "messageId": f"{uuid.uuid4()}",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1545082649183",
                "SenderId": "SenderId",
                "ApproximateFirstReceiveTimestamp": "1545082649185",
            },
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "awsRegion": "us-east-1",
        }

    return factory


@pytest.fixture(scope="module")
def kinesis_event_factory() -> Callable:
    def factory(body: str):
        seq = "".join(str(randint(0, 9)) for _ in range(52))
        return {
            "kinesis": {
                "kinesisSchemaVersion": "1.0",
                "partitionKey": "1",
                "sequenceNumber": seq,
                "data": str_to_b64(body),
                "approximateArrivalTimestamp": 1545084650.987,
            },
            "eventSource": "aws:kinesis",
            "eventVersion": "1.0",
            "eventID": f"shardId-000000000006:{seq}",
            "eventName": "aws:kinesis:record",
            "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-role",
            "awsRegion": "us-east-2",
            "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream",
        }

    return factory


@pytest.fixture(scope="module")
def dynamodb_event_factory() -> Callable:
    def factory(body: str):
        seq = "".join(str(randint(0, 9)) for _ in range(10))
        return {
            "eventID": "1",
            "eventVersion": "1.0",
            "dynamodb": {
                "Keys": {"Id": {"N": "101"}},
                "NewImage": {"Message": {"S": body}},
                "StreamViewType": "NEW_AND_OLD_IMAGES",
                "SequenceNumber": seq,
                "SizeBytes": 26,
            },
            "awsRegion": "us-west-2",
            "eventName": "INSERT",
            "eventSourceARN": "eventsource_arn",
            "eventSource": "aws:dynamodb",
        }

    return factory


@pytest.fixture(scope="module")
def record_handler() -> Callable:
    def handler(record):
        body = record["body"]
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def async_record_handler() -> Callable[..., Awaitable[Any]]:
    async def handler(record):
        body = record["body"]
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def kinesis_record_handler() -> Callable:
    def handler(record: KinesisStreamRecord):
        body = b64_to_str(record.kinesis.data)
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def dynamodb_record_handler() -> Callable:
    def handler(record: DynamoDBRecord):
        body = record.dynamodb.new_image.get("Message")
        if "fail" in body:
            raise ValueError("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def order_event_factory() -> Callable:
    def factory(item: Dict) -> str:
        return json.dumps({"item": item})

    return factory


def test_batch_processor_middleware_success_only(sqs_event_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("success"))
    second_record = SQSRecord(sqs_event_factory("success"))
    event = {"Records": [first_record.raw_event, second_record.raw_event]}

    processor = BatchProcessor(event_type=EventType.SQS)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert result["batchItemFailures"] == []


def test_batch_processor_middleware_with_failure(sqs_event_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("fail"))
    second_record = SQSRecord(sqs_event_factory("success"))
    third_record = SQSRecord(sqs_event_factory("fail"))
    event = {"Records": [first_record.raw_event, second_record.raw_event, third_record.raw_event]}

    processor = BatchProcessor(event_type=EventType.SQS)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert len(result["batchItemFailures"]) == 2


def test_batch_processor_context_success_only(sqs_event_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("success"))
    second_record = SQSRecord(sqs_event_factory("success"))
    records = [first_record.raw_event, second_record.raw_event]
    processor = BatchProcessor(event_type=EventType.SQS)

    # WHEN
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages == [
        ("success", first_record.body, first_record.raw_event),
        ("success", second_record.body, second_record.raw_event),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_context_with_failure(sqs_event_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("failure"))
    second_record = SQSRecord(sqs_event_factory("success"))
    third_record = SQSRecord(sqs_event_factory("fail"))
    records = [first_record.raw_event, second_record.raw_event, third_record.raw_event]
    processor = BatchProcessor(event_type=EventType.SQS)

    # WHEN
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages[1] == ("success", second_record.body, second_record.raw_event)
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [{"itemIdentifier": first_record.message_id}, {"itemIdentifier": third_record.message_id}],
    }


def test_batch_processor_kinesis_context_success_only(kinesis_event_factory, kinesis_record_handler):
    # GIVEN
    first_record = KinesisStreamRecord(kinesis_event_factory("success"))
    second_record = KinesisStreamRecord(kinesis_event_factory("success"))

    records = [first_record.raw_event, second_record.raw_event]
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)

    # WHEN
    with processor(records, kinesis_record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages == [
        ("success", b64_to_str(first_record.kinesis.data), first_record.raw_event),
        ("success", b64_to_str(second_record.kinesis.data), second_record.raw_event),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_kinesis_context_with_failure(kinesis_event_factory, kinesis_record_handler):
    # GIVEN
    first_record = KinesisStreamRecord(kinesis_event_factory("failure"))
    second_record = KinesisStreamRecord(kinesis_event_factory("success"))
    third_record = KinesisStreamRecord(kinesis_event_factory("failure"))

    records = [first_record.raw_event, second_record.raw_event, third_record.raw_event]
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)

    # WHEN
    with processor(records, kinesis_record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages[1] == ("success", b64_to_str(second_record.kinesis.data), second_record.raw_event)
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record.kinesis.sequence_number},
            {"itemIdentifier": third_record.kinesis.sequence_number},
        ],
    }


def test_batch_processor_kinesis_middleware_with_failure(kinesis_event_factory, kinesis_record_handler):
    # GIVEN
    first_record = KinesisStreamRecord(kinesis_event_factory("failure"))
    second_record = KinesisStreamRecord(kinesis_event_factory("success"))
    third_record = KinesisStreamRecord(kinesis_event_factory("failure"))
    event = {"Records": [first_record.raw_event, second_record.raw_event, third_record.raw_event]}

    processor = BatchProcessor(event_type=EventType.KinesisDataStreams)

    @batch_processor(record_handler=kinesis_record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert len(result["batchItemFailures"]) == 2


def test_batch_processor_dynamodb_context_success_only(dynamodb_event_factory, dynamodb_record_handler):
    # GIVEN
    first_record = dynamodb_event_factory("success")
    second_record = dynamodb_event_factory("success")
    records = [first_record, second_record]
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)

    # WHEN
    with processor(records, dynamodb_record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages == [
        ("success", first_record["dynamodb"]["NewImage"]["Message"]["S"], first_record),
        ("success", second_record["dynamodb"]["NewImage"]["Message"]["S"], second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_dynamodb_context_with_failure(dynamodb_event_factory, dynamodb_record_handler):
    # GIVEN
    first_record = dynamodb_event_factory("failure")
    second_record = dynamodb_event_factory("success")
    third_record = dynamodb_event_factory("failure")
    records = [first_record, second_record, third_record]
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)

    # WHEN
    with processor(records, dynamodb_record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    assert processed_messages[1] == ("success", second_record["dynamodb"]["NewImage"]["Message"]["S"], second_record)
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["dynamodb"]["SequenceNumber"]},
            {"itemIdentifier": third_record["dynamodb"]["SequenceNumber"]},
        ],
    }


def test_batch_processor_dynamodb_middleware_with_failure(dynamodb_event_factory, dynamodb_record_handler):
    # GIVEN
    first_record = dynamodb_event_factory("failure")
    second_record = dynamodb_event_factory("success")
    third_record = dynamodb_event_factory("failure")
    event = {"Records": [first_record, second_record, third_record]}

    processor = BatchProcessor(event_type=EventType.DynamoDBStreams)

    @batch_processor(record_handler=dynamodb_record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert len(result["batchItemFailures"]) == 2


def test_batch_processor_error_when_entire_batch_fails(sqs_event_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("fail"))
    second_record = SQSRecord(sqs_event_factory("fail"))
    event = {"Records": [first_record.raw_event, second_record.raw_event]}

    processor = BatchProcessor(event_type=EventType.SQS)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN calling `lambda_handler` in cold start
    with pytest.raises(BatchProcessingError) as e:
        lambda_handler(event, {})

    # THEN raise BatchProcessingError
    assert "All records failed processing. " in str(e.value)

    # WHEN calling `lambda_handler` in warm start
    with pytest.raises(BatchProcessingError) as e:
        lambda_handler(event, {})

    # THEN raise BatchProcessingError
    assert "All records failed processing. " in str(e.value)


def test_sqs_fifo_batch_processor_middleware_success_only(sqs_event_fifo_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_fifo_factory("success"))
    second_record = SQSRecord(sqs_event_fifo_factory("success"))
    event = {"Records": [first_record.raw_event, second_record.raw_event]}

    processor = SqsFifoPartialProcessor()

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert result["batchItemFailures"] == []


def test_sqs_fifo_batch_processor_middleware_with_failure(sqs_event_fifo_factory, record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_fifo_factory("success"))
    second_record = SQSRecord(sqs_event_fifo_factory("fail"))
    # this would normally succeed, but since it's a FIFO queue, it will be marked as failure
    third_record = SQSRecord(sqs_event_fifo_factory("success"))
    event = {"Records": [first_record.raw_event, second_record.raw_event, third_record.raw_event]}

    processor = SqsFifoPartialProcessor()

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert len(result["batchItemFailures"]) == 2
    assert result["batchItemFailures"][0]["itemIdentifier"] == second_record.message_id
    assert result["batchItemFailures"][1]["itemIdentifier"] == third_record.message_id


def test_sqs_fifo_batch_processor_middleware_with_skip_group_on_error(sqs_event_fifo_factory, record_handler):
    # GIVEN a batch of 5 records with 3 different MessageGroupID
    first_record = SQSRecord(sqs_event_fifo_factory("success", "1"))
    second_record = SQSRecord(sqs_event_fifo_factory("success", "1"))
    third_record = SQSRecord(sqs_event_fifo_factory("fail", "2"))
    fourth_record = SQSRecord(sqs_event_fifo_factory("success", "2"))
    fifth_record = SQSRecord(sqs_event_fifo_factory("fail", "3"))
    event = {
        "Records": [
            first_record.raw_event,
            second_record.raw_event,
            third_record.raw_event,
            fourth_record.raw_event,
            fifth_record.raw_event,
        ],
    }

    # WHEN the FIFO processor is set to continue processing even after encountering errors in specific MessageGroupID
    processor = SqsFifoPartialProcessor(skip_group_on_error=True)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN only failed messages should originate from MessageGroupID 3
    assert len(result["batchItemFailures"]) == 3
    assert result["batchItemFailures"][0]["itemIdentifier"] == third_record.message_id
    assert result["batchItemFailures"][1]["itemIdentifier"] == fourth_record.message_id
    assert result["batchItemFailures"][2]["itemIdentifier"] == fifth_record.message_id


def test_sqs_fifo_batch_processor_middleware_with_skip_group_on_error_first_message_fail(
    sqs_event_fifo_factory,
    record_handler,
):
    # GIVEN a batch of 5 records with 3 different MessageGroupID
    first_record = SQSRecord(sqs_event_fifo_factory("fail", "1"))
    second_record = SQSRecord(sqs_event_fifo_factory("success", "1"))
    third_record = SQSRecord(sqs_event_fifo_factory("fail", "2"))
    fourth_record = SQSRecord(sqs_event_fifo_factory("success", "2"))
    fifth_record = SQSRecord(sqs_event_fifo_factory("success", "3"))
    event = {
        "Records": [
            first_record.raw_event,
            second_record.raw_event,
            third_record.raw_event,
            fourth_record.raw_event,
            fifth_record.raw_event,
        ],
    }

    # WHEN the FIFO processor is set to continue processing even after encountering errors in specific MessageGroupID
    processor = SqsFifoPartialProcessor(skip_group_on_error=True)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN the handler is onvoked
    result = lambda_handler(event, {})

    # THEN messages from group 1 and 2 should fail, but not group 3
    assert len(result["batchItemFailures"]) == 4
    assert result["batchItemFailures"][0]["itemIdentifier"] == first_record.message_id
    assert result["batchItemFailures"][1]["itemIdentifier"] == second_record.message_id
    assert result["batchItemFailures"][2]["itemIdentifier"] == third_record.message_id
    assert result["batchItemFailures"][3]["itemIdentifier"] == fourth_record.message_id


def test_async_batch_processor_middleware_success_only(sqs_event_factory, async_record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("success"))
    second_record = SQSRecord(sqs_event_factory("success"))
    event = {"Records": [first_record.raw_event, second_record.raw_event]}

    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    @async_batch_processor(record_handler=async_record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert result["batchItemFailures"] == []


def test_async_batch_processor_middleware_with_failure(sqs_event_factory, async_record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("fail"))
    second_record = SQSRecord(sqs_event_factory("success"))
    third_record = SQSRecord(sqs_event_factory("fail"))
    event = {"Records": [first_record.raw_event, second_record.raw_event, third_record.raw_event]}

    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    @async_batch_processor(record_handler=async_record_handler, processor=processor)
    def lambda_handler(event, context):
        return processor.response()

    # WHEN
    result = lambda_handler(event, {})

    # THEN
    assert len(result["batchItemFailures"]) == 2


def test_async_batch_processor_context_success_only(sqs_event_factory, async_record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("success"))
    second_record = SQSRecord(sqs_event_factory("success"))
    records = [first_record.raw_event, second_record.raw_event]
    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    # WHEN
    with processor(records, async_record_handler) as batch:
        processed_messages = batch.async_process()

    # THEN
    assert processed_messages == [
        ("success", first_record.body, first_record.raw_event),
        ("success", second_record.body, second_record.raw_event),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_async_batch_processor_context_with_failure(sqs_event_factory, async_record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("failure"))
    second_record = SQSRecord(sqs_event_factory("success"))
    third_record = SQSRecord(sqs_event_factory("fail"))
    records = [first_record.raw_event, second_record.raw_event, third_record.raw_event]
    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    # WHEN
    with processor(records, async_record_handler) as batch:
        processed_messages = batch.async_process()

    # THEN
    assert processed_messages[1] == ("success", second_record.body, second_record.raw_event)
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [{"itemIdentifier": first_record.message_id}, {"itemIdentifier": third_record.message_id}],
    }


def test_process_partial_response(sqs_event_factory, record_handler):
    # GIVEN
    records = [sqs_event_factory("success"), sqs_event_factory("success")]
    batch = {"Records": records}
    processor = BatchProcessor(event_type=EventType.SQS)

    # WHEN
    ret = process_partial_response(batch, record_handler, processor)

    # THEN
    assert ret == {"batchItemFailures": []}


@pytest.mark.parametrize(
    "batch",
    [
        pytest.param(123456789, id="num"),
        pytest.param([], id="list"),
        pytest.param(False, id="bool"),
        pytest.param(object, id="object"),
        pytest.param(lambda x: x, id="callable"),
    ],
)
def test_process_partial_response_invalid_input(record_handler: Callable, batch: Any):
    # GIVEN
    processor = BatchProcessor(event_type=EventType.SQS)

    # WHEN/THEN
    with pytest.raises(ValueError):
        process_partial_response(batch, record_handler, processor)


def test_async_process_partial_response(sqs_event_factory, async_record_handler):
    # GIVEN
    records = [sqs_event_factory("success"), sqs_event_factory("success")]
    batch = {"Records": records}
    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    # WHEN
    ret = async_process_partial_response(batch, async_record_handler, processor)

    # THEN
    assert ret == {"batchItemFailures": []}


@pytest.mark.parametrize(
    "batch",
    [
        pytest.param(123456789, id="num"),
        pytest.param([], id="list"),
        pytest.param(False, id="bool"),
        pytest.param(object, id="object"),
        pytest.param(lambda x: x, id="callable"),
    ],
)
def test_async_process_partial_response_invalid_input(async_record_handler: Callable, batch: Any):
    # GIVEN
    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    # WHEN/THEN
    with pytest.raises(ValueError):
        async_process_partial_response(batch, record_handler, processor)

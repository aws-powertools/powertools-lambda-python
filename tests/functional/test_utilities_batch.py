import asyncio
import json
from random import randint
from typing import Callable, Dict, Optional

import pytest
from botocore.config import Config
from tests.functional.utils import b64_to_str, str_to_b64

from aws_lambda_powertools.asynchrony import async_lambda_handler
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    batch_processor,
    AsyncBatchProcessor,
    async_batch_processor,
)
from aws_lambda_powertools.utilities.batch.exceptions import BatchProcessingError
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    DynamoDBRecord,
)
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import (
    KinesisStreamRecord,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.parser import BaseModel, validator
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamChangedRecordModel, DynamoDBStreamRecordModel, KinesisDataStreamRecord as KinesisDataStreamRecordModel, \
    KinesisDataStreamRecordPayload, SqsRecordModel
from aws_lambda_powertools.utilities.parser.types import Literal


@pytest.fixture(scope="module")
def sqs_event_factory() -> Callable:
    def factory(body: str):
        return {
            "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1545082649183",
                "SenderId": "AIDAIENQZJOLO23YVJ4VO",
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
def async_record_handler() -> Callable:
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
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def config() -> Config:
    return Config(region_name="us-east-1")


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
        "batchItemFailures": [{"itemIdentifier": first_record.message_id}, {"itemIdentifier": third_record.message_id}]
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
        ]
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
        ]
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


def test_batch_processor_context_model(sqs_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderSqs(SqsRecordModel):
        body: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("body", pre=True)
        def transform_body_to_dict(cls, value: str):
            return json.loads(value)

    def record_handler(record: OrderSqs):
        return record.body.item

    order_event = order_event_factory({"type": "success"})
    first_record = sqs_event_factory(order_event)
    second_record = sqs_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_context_model_with_failure(sqs_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderSqs(SqsRecordModel):
        body: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("body", pre=True)
        def transform_body_to_dict(cls, value: str):
            return json.loads(value)

    def record_handler(record: OrderSqs):
        if "fail" in record.body.item["type"]:
            raise Exception("Failed to process record.")
        return record.body.item

    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})
    first_record = sqs_event_factory(order_event_fail)
    third_record = sqs_event_factory(order_event_fail)
    second_record = sqs_event_factory(order_event)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.SQS, model=OrderSqs)
    with processor(records, record_handler) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["messageId"]},
            {"itemIdentifier": third_record["messageId"]},
        ]
    }


def test_batch_processor_dynamodb_context_model(dynamodb_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderDynamoDB(BaseModel):
        Message: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("Message", pre=True)
        def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
            return json.loads(value["S"])

    class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
        NewImage: Optional[OrderDynamoDB]
        OldImage: Optional[OrderDynamoDB]

    class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
        dynamodb: OrderDynamoDBChangeRecord

    def record_handler(record: OrderDynamoDBRecord):
        return record.dynamodb.NewImage.Message.item

    order_event = order_event_factory({"type": "success"})
    first_record = dynamodb_event_factory(order_event)
    second_record = dynamodb_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_dynamodb_context_model_with_failure(dynamodb_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderDynamoDB(BaseModel):
        Message: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("Message", pre=True)
        def transform_message_to_dict(cls, value: Dict[Literal["S"], str]):
            return json.loads(value["S"])

    class OrderDynamoDBChangeRecord(DynamoDBStreamChangedRecordModel):
        NewImage: Optional[OrderDynamoDB]
        OldImage: Optional[OrderDynamoDB]

    class OrderDynamoDBRecord(DynamoDBStreamRecordModel):
        dynamodb: OrderDynamoDBChangeRecord

    def record_handler(record: OrderDynamoDBRecord):
        if "fail" in record.dynamodb.NewImage.Message.item["type"]:
            raise Exception("Failed to process record.")
        return record.dynamodb.NewImage.Message.item

    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})
    first_record = dynamodb_event_factory(order_event_fail)
    second_record = dynamodb_event_factory(order_event)
    third_record = dynamodb_event_factory(order_event_fail)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.DynamoDBStreams, model=OrderDynamoDBRecord)
    with processor(records, record_handler) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["dynamodb"]["SequenceNumber"]},
            {"itemIdentifier": third_record["dynamodb"]["SequenceNumber"]},
        ]
    }


def test_batch_processor_kinesis_context_parser_model(kinesis_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderKinesisPayloadRecord(KinesisDataStreamRecordPayload):
        data: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("data", pre=True)
        def transform_message_to_dict(cls, value: str):
            # Powertools KinesisDataStreamRecordModel already decodes b64 to str here
            return json.loads(value)

    class OrderKinesisRecord(KinesisDataStreamRecordModel):
        kinesis: OrderKinesisPayloadRecord

    def record_handler(record: OrderKinesisRecord):
        return record.kinesis.data.item

    order_event = order_event_factory({"type": "success"})
    first_record = kinesis_event_factory(order_event)
    second_record = kinesis_event_factory(order_event)
    records = [first_record, second_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, record_handler) as batch:
        processed_messages = batch.process()

    # THEN
    order_item = json.loads(order_event)["item"]
    assert processed_messages == [
        ("success", order_item, first_record),
        ("success", order_item, second_record),
    ]

    assert batch.response() == {"batchItemFailures": []}


def test_batch_processor_kinesis_context_parser_model_with_failure(kinesis_event_factory, order_event_factory):
    # GIVEN
    class Order(BaseModel):
        item: dict

    class OrderKinesisPayloadRecord(KinesisDataStreamRecordPayload):
        data: Order

        # auto transform json string
        # so Pydantic can auto-initialize nested Order model
        @validator("data", pre=True)
        def transform_message_to_dict(cls, value: str):
            # Powertools KinesisDataStreamRecordModel
            return json.loads(value)

    class OrderKinesisRecord(KinesisDataStreamRecordModel):
        kinesis: OrderKinesisPayloadRecord

    def record_handler(record: OrderKinesisRecord):
        if "fail" in record.kinesis.data.item["type"]:
            raise Exception("Failed to process record.")
        return record.kinesis.data.item

    order_event = order_event_factory({"type": "success"})
    order_event_fail = order_event_factory({"type": "fail"})

    first_record = kinesis_event_factory(order_event_fail)
    second_record = kinesis_event_factory(order_event)
    third_record = kinesis_event_factory(order_event_fail)
    records = [first_record, second_record, third_record]

    # WHEN
    processor = BatchProcessor(event_type=EventType.KinesisDataStreams, model=OrderKinesisRecord)
    with processor(records, record_handler) as batch:
        batch.process()

    # THEN
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [
            {"itemIdentifier": first_record["kinesis"]["sequenceNumber"]},
            {"itemIdentifier": third_record["kinesis"]["sequenceNumber"]},
        ]
    }


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


def test_async_batch_processor_middleware_success_only(sqs_event_factory, async_record_handler):
    # GIVEN
    first_record = SQSRecord(sqs_event_factory("success"))
    second_record = SQSRecord(sqs_event_factory("success"))
    event = {"Records": [first_record.raw_event, second_record.raw_event]}

    processor = AsyncBatchProcessor(event_type=EventType.SQS)

    @async_lambda_handler
    @async_batch_processor(record_handler=async_record_handler, processor=processor)
    async def lambda_handler(event, context):
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

    @async_lambda_handler
    @async_batch_processor(record_handler=async_record_handler, processor=processor)
    async def lambda_handler(event, context):
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
        async def process_messages():
            return await batch.async_process()

        processed_messages = asyncio.run(process_messages())

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
        async def process_messages():
            return await batch.async_process()

        processed_messages = asyncio.run(process_messages())

    # THEN
    assert processed_messages[1] == ("success", second_record.body, second_record.raw_event)
    assert len(batch.fail_messages) == 2
    assert batch.response() == {
        "batchItemFailures": [{"itemIdentifier": first_record.message_id}, {"itemIdentifier": third_record.message_id}]
    }

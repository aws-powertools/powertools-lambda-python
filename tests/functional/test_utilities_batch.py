import json
import math
from random import randint
from typing import Callable, Dict, Optional
from unittest.mock import patch

import pytest
from botocore.config import Config
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    PartialSQSProcessor,
    batch_processor,
    sqs_batch_processor,
)
from aws_lambda_powertools.utilities.batch.exceptions import BatchProcessingError, SQSBatchProcessingError
from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
from aws_lambda_powertools.utilities.data_classes.kinesis_stream_event import KinesisStreamRecord
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.parser import BaseModel, validator
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamChangedRecordModel, DynamoDBStreamRecordModel
from aws_lambda_powertools.utilities.parser.models import KinesisDataStreamRecord as KinesisDataStreamRecordModel
from aws_lambda_powertools.utilities.parser.models import KinesisDataStreamRecordPayload, SqsRecordModel
from aws_lambda_powertools.utilities.parser.types import Literal
from tests.functional.utils import b64_to_str, str_to_b64


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
def sns_event_factory() -> Callable:
    def factory(body: str):
        return {
            "EventVersion": "1.0",
            "EventSubscriptionArn": "arn:aws:sns:us-east-2:123456789012:sns-la ...",
            "EventSource": "aws:sns",
            "Sns": {
                "SignatureVersion": "1",
                "Timestamp": "2019-01-02T12:45:07.000Z",
                "Signature": "tcc6faL2yUC6dgZdmrwh1Y4cGa/ebXEkAi6RibDsvpi+tE/1+82j...65r==",
                "SigningCertUrl": "https://sns.us-east-2.amazonaws.com/SimpleNotification",
                "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                "Message": "Hello from SNS!",
                "MessageAttributes": {
                    "Test": {"Type": "String", "Value": "TestString"},
                    "TestBinary": {"Type": "Binary", "Value": "TestBinary"},
                },
                "Type": "Notification",
                "UnsubscribeUrl": "https://sns.us-east-2.amazonaws.com/?Action=Unsubscribe",
                "TopicArn": "arn:aws:sns:us-east-2:123456789012:sns-lambda",
                "Subject": "TestInvoke",
            },
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
        body = record.dynamodb.new_image.get("Message").get_value
        if "fail" in body:
            raise Exception("Failed to process record.")
        return body

    return handler


@pytest.fixture(scope="module")
def config() -> Config:
    return Config(region_name="us-east-1")


@pytest.fixture(scope="function")
def partial_processor(config) -> PartialSQSProcessor:
    return PartialSQSProcessor(config=config)


@pytest.fixture(scope="function")
def partial_processor_suppressed(config) -> PartialSQSProcessor:
    return PartialSQSProcessor(config=config, suppress_exception=True)


@pytest.fixture(scope="function")
def stubbed_partial_processor(config) -> PartialSQSProcessor:
    processor = PartialSQSProcessor(config=config)
    with Stubber(processor.client) as stubber:
        yield stubber, processor


@pytest.fixture(scope="function")
def stubbed_partial_processor_suppressed(config) -> PartialSQSProcessor:
    processor = PartialSQSProcessor(config=config, suppress_exception=True)
    with Stubber(processor.client) as stubber:
        yield stubber, processor


@pytest.fixture(scope="module")
def order_event_factory() -> Callable:
    def factory(item: Dict) -> str:
        return json.dumps({"item": item})

    return factory


@pytest.mark.parametrize(
    "success_messages_count",
    ([1, 18, 34]),
)
def test_partial_sqs_processor_context_with_failure(
    success_messages_count, sqs_event_factory, record_handler, partial_processor
):
    """
    Test processor with one failing record and multiple processed records
    """
    fail_record = sqs_event_factory("fail")
    success_records = [sqs_event_factory("success") for i in range(0, success_messages_count)]

    records = [fail_record, *success_records]

    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(partial_processor.client) as stubber:
        for _ in range(0, math.ceil((success_messages_count / partial_processor.max_message_batch))):
            stubber.add_response("delete_message_batch", response)
        with pytest.raises(SQSBatchProcessingError) as error:
            with partial_processor(records, record_handler) as ctx:
                ctx.process()

        assert len(error.value.child_exceptions) == 1
        stubber.assert_no_pending_responses()


def test_partial_sqs_processor_context_with_failure_exception(sqs_event_factory, record_handler, partial_processor):
    """
    Test processor with one failing record
    """
    fail_record = sqs_event_factory("fail")
    success_record = sqs_event_factory("success")

    records = [fail_record, success_record]

    with Stubber(partial_processor.client) as stubber:
        stubber.add_client_error(
            method="delete_message_batch", service_error_code="ServiceUnavailable", http_status_code=503
        )
        with pytest.raises(Exception) as error:
            with partial_processor(records, record_handler) as ctx:
                ctx.process()

        assert "ServiceUnavailable" in str(error.value)
        stubber.assert_no_pending_responses()


def test_partial_sqs_processor_context_only_success(sqs_event_factory, record_handler, partial_processor):
    """
    Test processor without failure
    """
    first_record = sqs_event_factory("success")
    second_record = sqs_event_factory("success")

    records = [first_record, second_record]

    with partial_processor(records, record_handler) as ctx:
        result = ctx.process()

    assert result == [
        ("success", first_record["body"], first_record),
        ("success", second_record["body"], second_record),
    ]


def test_partial_sqs_processor_context_multiple_calls(sqs_event_factory, record_handler, partial_processor):
    """
    Test processor without failure
    """
    first_record = sqs_event_factory("success")
    second_record = sqs_event_factory("success")

    records = [first_record, second_record]

    with partial_processor(records, record_handler) as ctx:
        ctx.process()

    with partial_processor([first_record], record_handler) as ctx:
        ctx.process()

    assert partial_processor.success_messages == [first_record]


def test_batch_processor_middleware_with_partial_sqs_processor(sqs_event_factory, record_handler, partial_processor):
    """
    Test middleware's integration with PartialSQSProcessor
    """

    @batch_processor(record_handler=record_handler, processor=partial_processor)
    def lambda_handler(event, context):
        return True

    fail_record = sqs_event_factory("fail")

    event = {"Records": [sqs_event_factory("fail"), sqs_event_factory("fail"), sqs_event_factory("success")]}
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(partial_processor.client) as stubber:
        stubber.add_response("delete_message_batch", response)
        with pytest.raises(SQSBatchProcessingError) as error:
            lambda_handler(event, {})

        assert len(error.value.child_exceptions) == 2
        stubber.assert_no_pending_responses()


@patch("aws_lambda_powertools.utilities.batch.sqs.PartialSQSProcessor")
def test_sqs_batch_processor_middleware(
    patched_sqs_processor, sqs_event_factory, record_handler, stubbed_partial_processor
):
    """
    Test middleware's integration with PartialSQSProcessor
    """

    @sqs_batch_processor(record_handler=record_handler)
    def lambda_handler(event, context):
        return True

    stubber, processor = stubbed_partial_processor
    patched_sqs_processor.return_value = processor

    fail_record = sqs_event_factory("fail")

    event = {"Records": [sqs_event_factory("fail"), sqs_event_factory("success")]}
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}
    stubber.add_response("delete_message_batch", response)
    with pytest.raises(SQSBatchProcessingError) as error:
        lambda_handler(event, {})

    assert len(error.value.child_exceptions) == 1
    stubber.assert_no_pending_responses()


def test_batch_processor_middleware_with_custom_processor(capsys, sqs_event_factory, record_handler, config):
    """
    Test middlewares' integration with custom batch processor
    """

    class CustomProcessor(PartialSQSProcessor):
        def failure_handler(self, record, exception):
            print("Oh no ! It's a failure.")
            return super().failure_handler(record, exception)

    processor = CustomProcessor(config=config)

    @batch_processor(record_handler=record_handler, processor=processor)
    def lambda_handler(event, context):
        return True

    fail_record = sqs_event_factory("fail")

    event = {"Records": [sqs_event_factory("fail"), sqs_event_factory("success")]}
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(processor.client) as stubber:
        stubber.add_response("delete_message_batch", response)
        with pytest.raises(SQSBatchProcessingError) as error:
            lambda_handler(event, {})

        stubber.assert_no_pending_responses()

    assert len(error.value.child_exceptions) == 1
    assert capsys.readouterr().out == "Oh no ! It's a failure.\n"


def test_batch_processor_middleware_suppressed_exceptions(
    sqs_event_factory, record_handler, partial_processor_suppressed
):
    """
    Test middleware's integration with PartialSQSProcessor
    """

    @batch_processor(record_handler=record_handler, processor=partial_processor_suppressed)
    def lambda_handler(event, context):
        return True

    fail_record = sqs_event_factory("fail")

    event = {"Records": [sqs_event_factory("fail"), sqs_event_factory("fail"), sqs_event_factory("success")]}
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(partial_processor_suppressed.client) as stubber:
        stubber.add_response("delete_message_batch", response)
        result = lambda_handler(event, {})

        stubber.assert_no_pending_responses()
        assert result is True


def test_partial_sqs_processor_suppressed_exceptions(sqs_event_factory, record_handler, partial_processor_suppressed):
    """
    Test processor without failure
    """

    first_record = sqs_event_factory("success")
    second_record = sqs_event_factory("fail")
    records = [first_record, second_record]

    fail_record = sqs_event_factory("fail")
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(partial_processor_suppressed.client) as stubber:
        stubber.add_response("delete_message_batch", response)
        with partial_processor_suppressed(records, record_handler) as ctx:
            ctx.process()

    assert partial_processor_suppressed.success_messages == [first_record]


@patch("aws_lambda_powertools.utilities.batch.sqs.PartialSQSProcessor")
def test_sqs_batch_processor_middleware_suppressed_exception(
    patched_sqs_processor, sqs_event_factory, record_handler, stubbed_partial_processor_suppressed
):
    """
    Test middleware's integration with PartialSQSProcessor
    """

    @sqs_batch_processor(record_handler=record_handler)
    def lambda_handler(event, context):
        return True

    stubber, processor = stubbed_partial_processor_suppressed
    patched_sqs_processor.return_value = processor

    fail_record = sqs_event_factory("fail")

    event = {"Records": [sqs_event_factory("fail"), sqs_event_factory("success")]}
    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}
    stubber.add_response("delete_message_batch", response)
    result = lambda_handler(event, {})

    stubber.assert_no_pending_responses()
    assert result is True


def test_partial_sqs_processor_context_only_failure(sqs_event_factory, record_handler, partial_processor):
    """
    Test processor with only failures
    """
    first_record = sqs_event_factory("fail")
    second_record = sqs_event_factory("fail")

    records = [first_record, second_record]
    with pytest.raises(SQSBatchProcessingError) as error:
        with partial_processor(records, record_handler) as ctx:
            ctx.process()

    assert len(error.value.child_exceptions) == 2


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

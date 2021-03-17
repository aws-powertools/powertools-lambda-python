from typing import Callable
from unittest.mock import patch

import pytest
from botocore.config import Config
from botocore.stub import Stubber

from aws_lambda_powertools.utilities.batch import PartialSQSProcessor, batch_processor, sqs_batch_processor
from aws_lambda_powertools.utilities.batch.exceptions import SQSBatchProcessingError


@pytest.fixture(scope="module")
def sqs_event_factory() -> Callable:
    def factory(body: str):
        return {
            "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
            "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a",
            "body": body,
            "attributes": {},
            "messageAttributes": {},
            "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-2:123456789012:my-queue",
            "awsRegion": "us-east-1",
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


def test_partial_sqs_processor_context_with_failure(sqs_event_factory, record_handler, partial_processor):
    """
    Test processor with one failing record
    """
    fail_record = sqs_event_factory("fail")
    success_record = sqs_event_factory("success")

    records = [fail_record, success_record]

    response = {"Successful": [{"Id": fail_record["messageId"]}], "Failed": []}

    with Stubber(partial_processor.client) as stubber:
        stubber.add_response("delete_message_batch", response)

        with pytest.raises(SQSBatchProcessingError) as error:
            with partial_processor(records, record_handler) as ctx:
                ctx.process()

        assert len(error.value.child_exceptions) == 1
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

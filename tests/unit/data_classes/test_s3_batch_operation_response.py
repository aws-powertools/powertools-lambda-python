import pytest

from aws_lambda_powertools.utilities.data_classes import (
    S3BatchOperationEvent,
    S3BatchOperationResponse,
    S3BatchOperationResponseRecord,
)
from tests.functional.utils import load_event


def test_result_as_succeeded():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    result_string = "Successfully processed"
    result = task.build_task_batch_response("Succeeded", result_string)

    assert_result(result, parsed_event.task.task_id, "Succeeded", result_string)


def test_result_as_temporary_failure():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    result_string = "Temporary failure"
    result = task.build_task_batch_response("TemporaryFailure", result_string)

    assert_result(result, parsed_event.task.task_id, "TemporaryFailure", result_string)


def test_result_as_permanent_failure():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    result_string = "Permanent failure"
    result = task.build_task_batch_response("PermanentFailure", result_string)

    assert_result(result, parsed_event.task.task_id, "PermanentFailure", result_string)


def assert_result(
    result: S3BatchOperationResponseRecord,
    task_id: str,
    expected_result_code: str,
    expected_result_string: str,
):
    assert result.result_code == expected_result_code
    assert result.result_string == expected_result_string

    meta = result.asdict()

    assert meta == {
        "taskId": task_id,
        "resultCode": expected_result_code,
        "resultString": expected_result_string,
    }


def test_response():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    response = S3BatchOperationResponse(
        parsed_event.invocation_schema_version,
        parsed_event.invocation_id,
        "PermanentFailure",
    )

    result_string = "Successfully processed"
    result = task.build_task_batch_response("Succeeded", result_string)

    response.add_result(result)

    assert len(response.results) == 1
    assert response.treat_missing_keys_as == "PermanentFailure"
    assert response.invocation_schema_version == parsed_event.invocation_schema_version
    assert response.invocation_id == parsed_event.invocation_id

    assert response.asdict() == {
        "invocationSchemaVersion": parsed_event.invocation_schema_version,
        "treatMissingKeysAs": "PermanentFailure",
        "invocationId": parsed_event.invocation_id,
        "results": [
            {
                "taskId": result.task_id,
                "resultCode": result.result_code,
                "resultString": result.result_string,
            },
        ],
    }


def test_response_multiple_results():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    response = S3BatchOperationResponse(parsed_event.invocation_schema_version, parsed_event.invocation_id, "Succeeded")

    result_string = "Successfully processed"
    result = task.build_task_batch_response("Succeeded", result_string)

    response.add_result(result)

    # add another result
    response.add_result(result)

    with pytest.raises(ValueError, match=r"Response must have exactly one result, but got *"):
        response.asdict()


def test_response_no_results():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    response = S3BatchOperationResponse(parsed_event.invocation_schema_version, parsed_event.invocation_id, "Succeeded")

    with pytest.raises(ValueError, match=r"Response must have exactly one result, but got *"):
        response.asdict()


def test_invalid_treating_missing_key():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    with pytest.warns(UserWarning, match="The value *"):
        S3BatchOperationResponse(parsed_event.invocation_schema_version, parsed_event.invocation_id, "invalid_value")


def test_invalid_record_status():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    task = parsed_event.task

    response = S3BatchOperationResponse(parsed_event.invocation_schema_version, parsed_event.invocation_id, "Succeeded")

    result_string = "Successfully processed"
    result = task.build_task_batch_response("invalid_value", result_string)
    response.add_result(result)

    with pytest.warns(UserWarning, match="The resultCode *"):
        response.asdict()

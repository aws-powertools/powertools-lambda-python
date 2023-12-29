# zzz from urllib.parse import quote_plus

from aws_lambda_powertools.utilities.data_classes import S3BatchOperationEvent
from tests.functional.utils import load_event


def test_s3_batch_operation_schema_v1():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    tasks = list(parsed_event.tasks)
    assert len(tasks) == 1
    task = tasks[0]
    task_raw = raw_event["tasks"][0]

    assert task.task_id == task_raw["taskId"]
    assert task.s3_version_id == task_raw["s3VersionId"]
    assert task.s3_bucket_arn == task_raw["s3BucketArn"]
    assert task.s3_bucket == task_raw["s3BucketArn"].split(":::")[-1]
    assert task.s3_key == task_raw["s3Key"]

    job = parsed_event.job
    assert job.id == raw_event["job"]["id"]
    assert job.user_arguments is None

    assert parsed_event.invocation_schema_version == raw_event["invocationSchemaVersion"]
    assert parsed_event.invocation_id == raw_event["invocationId"]


def test_s3_batch_operation_schema_v2():
    raw_event = load_event("s3BatchOperationEventSchemaV2.json")
    parsed_event = S3BatchOperationEvent(raw_event)

    tasks = list(parsed_event.tasks)
    assert len(tasks) == 1
    task = tasks[0]
    task_raw = raw_event["tasks"][0]

    assert task.task_id == task_raw["taskId"]
    assert task.s3_version_id == task_raw["s3VersionId"]
    assert task.s3_bucket_arn is None
    assert task.s3_bucket == task_raw["s3Bucket"]
    assert task.s3_key == task_raw["s3Key"]

    job = parsed_event.job
    assert job.id == raw_event["job"]["id"]
    assert job.user_arguments == raw_event["job"]["userArguments"]

    assert parsed_event.invocation_schema_version == raw_event["invocationSchemaVersion"]
    assert parsed_event.invocation_id == raw_event["invocationId"]

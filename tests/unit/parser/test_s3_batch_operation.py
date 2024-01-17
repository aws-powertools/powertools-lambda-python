from aws_lambda_powertools.utilities.parser.models import S3BatchOperationModel
from tests.functional.utils import load_event


def test_s3_batch_operation_v1_trigger_event():
    raw_event = load_event("s3BatchOperationEventSchemaV1.json")
    parsed_event: S3BatchOperationModel = S3BatchOperationModel(**raw_event)

    tasks = list(parsed_event.tasks)
    assert len(tasks) == 1

    assert parsed_event.invocationId == raw_event["invocationId"]
    assert parsed_event.invocationSchemaVersion == raw_event["invocationSchemaVersion"]
    assert parsed_event.job.id == raw_event["job"]["id"]

    assert tasks[0].taskId == raw_event["tasks"][0]["taskId"]
    assert tasks[0].s3Key == raw_event["tasks"][0]["s3Key"]
    assert tasks[0].s3VersionId == raw_event["tasks"][0]["s3VersionId"]
    assert tasks[0].s3BucketArn == raw_event["tasks"][0]["s3BucketArn"]
    assert tasks[0].s3Bucket == "powertools-dataset"


def test_s3_batch_operation_v2_trigger_event():
    raw_event = load_event("s3BatchOperationEventSchemaV2.json")
    parsed_event: S3BatchOperationModel = S3BatchOperationModel(**raw_event)

    tasks = list(parsed_event.tasks)
    assert len(tasks) == 1

    assert parsed_event.invocationId == raw_event["invocationId"]
    assert parsed_event.invocationSchemaVersion == raw_event["invocationSchemaVersion"]
    assert parsed_event.job.id == raw_event["job"]["id"]
    assert parsed_event.job.userArguments == raw_event["job"]["userArguments"]

    assert tasks[0].taskId == raw_event["tasks"][0]["taskId"]
    assert tasks[0].s3Key == raw_event["tasks"][0]["s3Key"]
    assert tasks[0].s3VersionId == raw_event["tasks"][0]["s3VersionId"]
    assert tasks[0].s3Bucket == raw_event["tasks"][0]["s3Bucket"]

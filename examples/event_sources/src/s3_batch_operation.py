import boto3
from botocore.exceptions import ClientError

from aws_lambda_powertools.utilities.data_classes import S3BatchOperationEvent, S3BatchOperationResponse, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=S3BatchOperationEvent)
def lambda_handler(event: S3BatchOperationEvent, context: LambdaContext):
    response = S3BatchOperationResponse(event.invocation_schema_version, event.invocation_id, "PermanentFailure")

    task = event.task
    src_key: str = task.s3_key
    src_bucket: str = task.s3_bucket

    s3 = boto3.client("s3", region_name="us-east-1")

    try:
        dest_bucket, dest_key = do_some_work(s3, src_bucket, src_key)
        result = task.build_task_batch_response("Succeeded", f"s3://{dest_bucket}/{dest_key}")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        if error_code == "RequestTimeout":
            result = task.build_task_batch_response("TemporaryFailure", "Retry request to Amazon S3 due to timeout.")
        else:
            result = task.build_task_batch_response("PermanentFailure", f"{error_code}: {error_message}")
    except Exception as e:
        result = task.build_task_batch_response("PermanentFailure", str(e))
    finally:
        response.add_result(result)

    return response.asdict()


def do_some_work(s3_client, src_bucket: str, src_key: str):
    ...

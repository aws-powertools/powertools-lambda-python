from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper

# list of valid result code. Used both in S3BatchOperationResponse and S3BatchOperationResponseRecord
VALID_RESULT_CODES: tuple[str, str, str] = ("Succeeded", "TemporaryFailure", "PermanentFailure")
RESULT_CODE_TYPE = Literal["Succeeded", "TemporaryFailure", "PermanentFailure"]

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(repr=False, order=False)
class S3BatchOperationResponseRecord:
    task_id: str
    result_code: RESULT_CODE_TYPE
    result_string: str | None = None

    def asdict(self) -> dict[str, Any]:
        if self.result_code not in VALID_RESULT_CODES:
            warnings.warn(
                stacklevel=2,
                message=f"The resultCode {self.result_code} is not valid. "
                f"Choose from {', '.join(map(repr, VALID_RESULT_CODES))}.",
            )

        return {
            "taskId": self.task_id,
            "resultCode": self.result_code,
            "resultString": self.result_string,
        }


@dataclass(repr=False, order=False)
class S3BatchOperationResponse:
    """S3 Batch Operations response object

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/services-s3-batch.html
    - https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops-invoke-lambda.html#batch-ops-invoke-lambda-custom-functions
    - https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_LambdaInvokeOperation.html#AmazonS3-Type-control_LambdaInvokeOperation-InvocationSchemaVersion

    Parameters
    ----------
    invocation_schema_version : str
        Specifies the schema version for the payload that Batch Operations sends when invoking
        an AWS Lambda function., either '1.0' or '2.0'. This must be copied from the event.

    invocation_id : str
        The identifier of the invocation request. This must be copied from the event.

    treat_missing_keys_as : Literal["Succeeded", "TemporaryFailure", "PermanentFailure"]
        Undocumented parameter, defaults to "Succeeded"

    results : list[S3BatchOperationResult]
        Results of each S3 Batch Operations task,
        optional parameter at start. Can be added later using `add_result` function.

    Examples
    --------

    **S3 Batch Operations**

    ```python
        import boto3

        from botocore.exceptions import ClientError

        from aws_lambda_powertools.utilities.data_classes import (
            S3BatchOperationEvent,
            S3BatchOperationResponse,
            event_source
        )
        from aws_lambda_powertools.utilities.typing import LambdaContext


        @event_source(data_class=S3BatchOperationEvent)
        def lambda_handler(event: S3BatchOperationEvent, context: LambdaContext):
            response = S3BatchOperationResponse(
                event.invocation_schema_version,
                event.invocation_id,
                "PermanentFailure"
                )

            result = None
            task = event.task
            src_key: str = task.s3_key
            src_bucket: str = task.s3_bucket

            s3 = boto3.client("s3", region_name='us-east-1')

            try:
                dest_bucket, dest_key = do_some_work(s3, src_bucket, src_key)
                result = task.build_task_batch_response("Succeeded", f"s3://{dest_bucket}/{dest_key}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                if error_code == 'RequestTimeout':
                    result = task.build_task_batch_response("TemporaryFailure", "Timeout - trying again")
                else:
                    result = task.build_task_batch_response("PermanentFailure", f"{error_code}: {error_message}")
            except Exception as e:
                result = task.build_task_batch_response("PermanentFailure", str(e))
            finally:
                response.add_result(result)

            return response.asdict()
    ```
    """

    invocation_schema_version: str
    invocation_id: str
    treat_missing_keys_as: RESULT_CODE_TYPE = "Succeeded"
    results: list[S3BatchOperationResponseRecord] = field(default_factory=list)

    def __post_init__(self):
        if self.treat_missing_keys_as not in VALID_RESULT_CODES:
            warnings.warn(
                stacklevel=2,
                message=f"The value {self.treat_missing_keys_as} is not valid for treat_missing_keys_as, "
                f"Choose from {', '.join(map(repr, VALID_RESULT_CODES))}.",
            )

    def add_result(self, result: S3BatchOperationResponseRecord):
        self.results.append(result)

    def asdict(self) -> dict:
        result_count = len(self.results)

        if result_count != 1:
            raise ValueError(f"Response must have exactly one result, but got {result_count}")

        return {
            "invocationSchemaVersion": self.invocation_schema_version,
            "treatMissingKeysAs": self.treat_missing_keys_as,
            "invocationId": self.invocation_id,
            "results": [result.asdict() for result in self.results],
        }


class S3BatchOperationJob(DictWrapper):
    @property
    def get_id(self) -> str:
        # Note: this name conflicts with existing python builtins
        return self["id"]

    @property
    def user_arguments(self) -> dict[str, str]:
        """Get user arguments provided for this job (only for invocation schema 2.0)"""
        return self.get("userArguments") or {}


class S3BatchOperationTask(DictWrapper):
    @property
    def task_id(self) -> str:
        """Get the task id"""
        return self["taskId"]

    @property
    def s3_key(self) -> str:
        """Get the object key using unquote_plus"""
        return unquote_plus(self["s3Key"])

    @property
    def s3_version_id(self) -> str | None:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self.get("s3VersionId")

    @property
    def s3_bucket_arn(self) -> str | None:
        """Get the s3 bucket arn (present only for invocationSchemaVersion '1.0')"""
        return self.get("s3BucketArn")

    @property
    def s3_bucket(self) -> str:
        """
        Get the s3 bucket, either from 's3Bucket' property (invocationSchemaVersion '2.0')
        or from 's3BucketArn' (invocationSchemaVersion '1.0')
        """
        if self.s3_bucket_arn:
            return self.s3_bucket_arn.split(":::")[-1]
        return self["s3Bucket"]

    def build_task_batch_response(
        self,
        result_code: Literal["Succeeded", "TemporaryFailure", "PermanentFailure"] = "Succeeded",
        result_string: str = "",
    ) -> S3BatchOperationResponseRecord:
        """Create a S3BatchOperationResponseRecord directly using the task_id and given values

        Parameters
        ----------
        result_code : Literal["Succeeded", "TemporaryFailure", "PermanentFailure"] = "Succeeded"
            task result, supported value: "Succeeded", "TemporaryFailure", "PermanentFailure"
        result_string : str
            string to identify in the report
        """
        return S3BatchOperationResponseRecord(
            task_id=self.task_id,
            result_code=result_code,
            result_string=result_string,
        )


class S3BatchOperationEvent(DictWrapper):
    """Amazon S3BatchOperation Event

    Documentation:
    --------------
    - https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops-invoke-lambda.html
    """

    @property
    def invocation_id(self) -> str:
        """Get the identifier of the invocation request"""
        return self["invocationId"]

    @property
    def invocation_schema_version(self) -> Literal["1.0", "2.0"]:
        """
        Get the schema version for the payload that Batch Operations sends when invoking an
        AWS Lambda function. Either '1.0' or '2.0'.
        """
        return self["invocationSchemaVersion"]

    @property
    def tasks(self) -> Iterator[S3BatchOperationTask]:
        """Get s3 batch operation tasks"""
        for task in self["tasks"]:
            yield S3BatchOperationTask(task)

    @property
    def task(self) -> S3BatchOperationTask:
        """Get the first s3 batch operation task"""
        return next(self.tasks)

    @property
    def job(self) -> S3BatchOperationJob:
        """Get the s3 batch operation job"""
        return S3BatchOperationJob(self["job"])

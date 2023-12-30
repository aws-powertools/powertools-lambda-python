from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import unquote_plus

from typing_extensions import Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class S3BatchOperationJob(DictWrapper):
    @property
    def id(self) -> str:  # noqa: A003
        return self["id"]

    @property
    def user_arguments(self) -> Optional[Dict[str, str]]:
        """Get user arguments provided for this job (only for invocation schema 2.0)"""
        return self.get("userArguments")


class S3BatchOperationTask(DictWrapper):
    @property
    def task_id(self) -> str:
        """Get the task id"""
        return self["taskId"]

    @property
    def s3_key(self) -> str:
        """Get the object key unquote_plus using strict utf-8 encoding"""
        # note: AWS documentation example is using unquote but this actually
        # contradicts what happens in practice. The key is url encoded with %20
        # in the inventory file but in the event it is sent with +. So use unquote_plus
        return unquote_plus(self["s3Key"], encoding="utf-8", errors="strict")

    @property
    def s3_version_id(self) -> Optional[str]:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self.get("s3VersionId")

    @property
    def s3_bucket_arn(self) -> Optional[str]:
        """Get the s3 bucket arn (present only for invocationSchemaVersion '1.0')"""
        return self.get("s3BucketArn")

    @property
    def s3_bucket(self) -> str:
        """ "
        Get the s3 bucket, either from 's3Bucket' property (invocationSchemaVersion '2.0')
        or from 's3BucketArn' (invocationSchemaVersion '1.0')
        """
        if self.s3_bucket_arn:
            return self.s3_bucket_arn.split(":::")[-1]
        return self["s3Bucket"]


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
    def invocation_schema_version(self) -> str:
        """ "
        Get the schema version for the payload that Batch Operations sends when invoking an
        AWS Lambda function. Either '1.0' or '2.0'.
        """
        return self["invocationSchemaVersion"]

    @property
    def tasks(self) -> Iterator[S3BatchOperationTask]:
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


# list of valid result code. Used both in S3BatchOperationResult and S3BatchOperationResponse
VALID_RESULT_CODE_TYPES: Tuple[str, str, str] = ("Succeeded", "TemporaryFailure", "PermanentFailure")


@dataclass(repr=False, order=False)
class S3BatchOperationResult:
    task_id: str
    result_code: Literal["Succeeded", "TemporaryFailure", "PermanentFailure"]
    result_string: Optional[str] = None

    def __post_init__(self):
        if self.result_code not in VALID_RESULT_CODE_TYPES:
            raise ValueError(f"Invalid result_code: {self.result_code}")

    def asdict(self) -> Dict[str, Any]:
        return {
            "taskId": self.task_id,
            "resultCode": self.result_code,
            "resultString": self.result_string,
        }

    @classmethod
    def as_succeeded(cls, task: S3BatchOperationTask, result_string: Optional[str] = None) -> "S3BatchOperationResult":
        """Create a `Succeeded` result for a given task"""
        return S3BatchOperationResult(task.task_id, "Succeeded", result_string)

    @classmethod
    def as_permanent_failure(
        cls,
        task: S3BatchOperationTask,
        result_string: Optional[str] = None,
    ) -> "S3BatchOperationResult":
        """Create a `PermanentFailure` result for a given task"""
        return S3BatchOperationResult(task.task_id, "PermanentFailure", result_string)

    @classmethod
    def as_temporary_failure(
        cls,
        task: S3BatchOperationTask,
        result_string: Optional[str] = None,
    ) -> "S3BatchOperationResult":
        """Create a `TemporaryFailure` result for a given task"""
        return S3BatchOperationResult(task.task_id, "TemporaryFailure", result_string)


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
        undocumented parameter, defaults to "PermanentFailure"

    results : List[S3BatchOperationResult]
        results of each S3 Batch Operations task,
        optional parameter at start. can be added later using `add_result` function.

    Examples
    --------

    **S3 Batch Operations**

    ```python
    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.utilities.data_classes import (
        S3BatchOperationEvent,
        S3BatchOperationResponse,
        S3BatchOperationResult
    )

    def lambda_handler(event: dict, context: LambdaContext):
        s3_event = S3BatchOperationEvent(event)
        response = S3BatchOperationResponse(s3_event.invocation_schema_version, s3_event.invocation_id)
        result = None

        task = s3_event.task
        try:
            do_work(task.s3_bucket, task.s3_key)
            result = S3BatchOperationResult.as_succeeded(task)
        except TimeoutError as e:
            result = S3BatchOperationResult.as_temporary_failure(task, str(e))
        except Exception as e:
            result = S3BatchOperationResult.as_permanent_failure(task, str(e))
        finally:
            response.add_result(result)

        return response.asdict()
    ```
    """

    invocation_schema_version: str
    invocation_id: str
    treat_missing_keys_as: Literal["Succeeded", "TemporaryFailure", "PermanentFailure"] = "PermanentFailure"
    results: List[S3BatchOperationResult] = field(default_factory=list)

    def __post_init__(self):
        if self.treat_missing_keys_as not in VALID_RESULT_CODE_TYPES:
            raise ValueError(f"Invalid treat_missing_keys_as: {self.treat_missing_keys_as}")

    def add_result(self, result: S3BatchOperationResult):
        self.results.append(result)

    def asdict(self) -> Dict:
        if not self.results:
            raise ValueError("Response must have one result")
        if len(self.results) > 1:
            raise ValueError("Response cannot have more than one result")

        return {
            "invocationSchemaVersion": self.invocation_schema_version,
            "treatMissingKeysAs": self.treat_missing_keys_as,
            "invocationId": self.invocation_id,
            "results": [result.asdict() for result in self.results],
        }

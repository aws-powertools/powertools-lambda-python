from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

from aws_lambda_powertools.utilities.parser.types import Literal


class S3BatchOperationTaskModel(BaseModel):
    taskId: str
    s3Key: str
    s3VersionId: Optional[str] = None
    s3BucketArn: Optional[str] = None
    s3Bucket: Optional[str] = None

    @validator("s3Bucket", pre=True, always=True)
    def validate_bucket(cls, current_value, values):
        # Get the s3 bucket, either from 's3Bucket' property (invocationSchemaVersion '2.0')
        # or from 's3BucketArn' (invocationSchemaVersion '1.0')
        if values.get("s3BucketArn") and not current_value:
            # Replace s3Bucket value with the value from s3BucketArn
            return values["s3BucketArn"].split(":::")[-1]
        return current_value


class S3BatchOperationJobModel(BaseModel):
    id: str
    userArguments: Optional[Dict[str, Any]] = None


class S3BatchOperationModel(BaseModel):
    invocationId: str
    invocationSchemaVersion: Literal["1.0", "2.0"]
    job: S3BatchOperationJobModel
    tasks: List[S3BatchOperationTaskModel]

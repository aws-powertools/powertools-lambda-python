from typing import Any, Dict, List, Literal

from pydantic import BaseModel, model_validator


class S3BatchOperationTaskModel(BaseModel):
    taskId: str
    s3Key: str
    s3VersionId: str | None = None
    s3BucketArn: str | None = None
    s3Bucket: str | None = None

    @model_validator(mode="before")
    def validate_s3bucket(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("s3BucketArn") and not values.get("s3Bucket"):
            values["s3Bucket"] = values["s3BucketArn"].split(":::")[-1]

        return values


class S3BatchOperationJobModel(BaseModel):
    id: str
    userArguments: Dict[str, Any] | None = None


class S3BatchOperationModel(BaseModel):
    invocationId: str
    invocationSchemaVersion: Literal["1.0", "2.0"]
    job: S3BatchOperationJobModel
    tasks: List[S3BatchOperationTaskModel]

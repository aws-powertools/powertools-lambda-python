from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, model_validator


class S3BatchOperationTaskModel(BaseModel):
    taskId: str
    s3Key: str
    s3VersionId: Optional[str] = None
    s3BucketArn: Optional[str] = None
    s3Bucket: Optional[str] = None

    @model_validator(mode="before")
    def validate_s3bucket(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("s3BucketArn") and not values.get("s3Bucket"):
            values["s3Bucket"] = values["s3BucketArn"].split(":::")[-1]

        return values


class S3BatchOperationJobModel(BaseModel):
    id: str
    userArguments: Optional[Dict[str, Any]] = None


class S3BatchOperationModel(BaseModel):
    invocationId: str
    invocationSchemaVersion: Literal["1.0", "2.0"]
    job: S3BatchOperationJobModel
    tasks: List[S3BatchOperationTaskModel]

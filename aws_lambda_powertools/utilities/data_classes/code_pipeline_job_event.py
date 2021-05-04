import json
from typing import Any, Dict, List, Optional
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CodePipelineConfiguration(DictWrapper):
    @property
    def function_name(self) -> str:
        """Function name"""
        return self["FunctionName"]

    @property
    def user_parameters(self) -> str:
        """User parameters"""
        return self["UserParameters"]

    @property
    def decoded_user_parameters(self) -> Dict[str, Any]:
        """Json Decoded user parameters"""
        return json.loads(self.user_parameters)


class CodePipelineActionConfiguration(DictWrapper):
    """CodePipeline Action Configuration"""

    @property
    def configuration(self) -> CodePipelineConfiguration:
        return CodePipelineConfiguration(self["configuration"])


class CodePipelineS3Location(DictWrapper):
    @property
    def bucket_name(self) -> str:
        return self["bucketName"]

    @property
    def key(self) -> str:
        """Raw S3 object key"""
        return self["objectKey"]

    @property
    def object_key(self) -> str:
        """Unquote plus of the S3 object key"""
        return unquote_plus(self["objectKey"])


class CodePipelineLocation(DictWrapper):
    @property
    def get_type(self) -> str:
        """Location type eg: S3"""
        return self["type"]

    @property
    def s3_location(self) -> CodePipelineS3Location:
        """S3 location"""
        return CodePipelineS3Location(self["s3Location"])


class CodePipelineArtifact(DictWrapper):
    @property
    def name(self) -> str:
        """Name"""
        return self["name"]

    @property
    def revision(self) -> Optional[str]:
        return self.get("revision")

    @property
    def location(self) -> CodePipelineLocation:
        return CodePipelineLocation(self["location"])


class CodePipelineArtifactCredentials(DictWrapper):
    @property
    def access_key_id(self) -> str:
        return self["accessKeyId"]

    @property
    def secret_access_key(self) -> str:
        return self["secretAccessKey"]

    @property
    def session_token(self) -> str:
        return self["sessionToken"]

    @property
    def expiration_time(self) -> Optional[int]:
        return self.get("expirationTime")


class CodePipelineData(DictWrapper):
    """CodePipeline Job Data"""

    @property
    def action_configuration(self) -> CodePipelineActionConfiguration:
        """CodePipeline action configuration"""
        return CodePipelineActionConfiguration(self["actionConfiguration"])

    @property
    def input_artifacts(self) -> List[CodePipelineArtifact]:
        """Represents a CodePipeline input artifact"""
        return [CodePipelineArtifact(item) for item in self["inputArtifacts"]]

    @property
    def output_artifacts(self) -> List[CodePipelineArtifact]:
        """Represents a CodePipeline output artifact"""
        return [CodePipelineArtifact(item) for item in self["outputArtifacts"]]

    @property
    def artifact_credentials(self) -> CodePipelineArtifactCredentials:
        """Represents a CodePipeline artifact credentials"""
        return CodePipelineArtifactCredentials(self["artifactCredentials"])

    @property
    def continuation_token(self) -> Optional[str]:
        """A continuation token if continuing job"""
        return self.get("continuationToken")


class CodePipelineJobEvent(DictWrapper):
    """AWS CodePipeline Job Event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html
    - https://docs.aws.amazon.com/lambda/latest/dg/services-codepipeline.html
    """

    @property
    def get_id(self) -> str:
        """Job id"""
        return self["CodePipeline.job"]["id"]

    @property
    def account_id(self) -> str:
        """Account id"""
        return self["CodePipeline.job"]["accountId"]

    @property
    def data(self) -> CodePipelineData:
        """Code pipeline jab data"""
        return CodePipelineData(self["CodePipeline.job"]["data"])

    @property
    def user_parameters(self) -> str:
        """User parameters"""
        return self.data.action_configuration.configuration.user_parameters

    @property
    def decoded_user_parameters(self) -> Dict[str, Any]:
        """Json Decoded user parameters"""
        return self.data.action_configuration.configuration.decoded_user_parameters

    @property
    def input_bucket_name(self) -> str:
        """Get the first input artifact bucket name"""
        return self.data.input_artifacts[0].location.s3_location.bucket_name

    @property
    def input_object_key(self) -> str:
        """Get the first input artifact order key unquote plus"""
        return self.data.input_artifacts[0].location.s3_location.object_key

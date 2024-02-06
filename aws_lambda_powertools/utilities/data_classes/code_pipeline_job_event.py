import tempfile
import zipfile
from functools import cached_property
from typing import Any, Dict, List, Optional
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CodePipelineConfiguration(DictWrapper):
    @property
    def function_name(self) -> str:
        """Function name"""
        return self["FunctionName"]

    @property
    def user_parameters(self) -> Optional[str]:
        """User parameters"""
        return self.get("UserParameters", None)

    @cached_property
    def decoded_user_parameters(self) -> Optional[Dict[str, Any]]:
        """Json Decoded user parameters"""
        if self.user_parameters is not None:
            return self._json_deserializer(self.user_parameters)

        return None


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
    _sensitive_properties = ["secret_access_key", "session_token"]

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


class CodePipelineEncryptionKey(DictWrapper):
    @property
    def get_id(self) -> str:
        return self["id"]

    @property
    def get_type(self) -> str:
        return self["type"]


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

    @property
    def encryption_key(self) -> Optional[CodePipelineEncryptionKey]:
        """Represents a CodePipeline encryption key"""
        key_data = self.get("encryptionKey")
        return CodePipelineEncryptionKey(key_data) if key_data is not None else None


class CodePipelineJobEvent(DictWrapper):
    """AWS CodePipeline Job Event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html
    - https://docs.aws.amazon.com/lambda/latest/dg/services-codepipeline.html
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self._job = self["CodePipeline.job"]

    @property
    def get_id(self) -> str:
        """Job id"""
        return self._job["id"]

    @property
    def account_id(self) -> str:
        """Account id"""
        return self._job["accountId"]

    @property
    def data(self) -> CodePipelineData:
        """Code pipeline jab data"""
        return CodePipelineData(self._job["data"])

    @property
    def user_parameters(self) -> Optional[str]:
        """Action configuration user parameters"""
        return self.data.action_configuration.configuration.user_parameters

    @property
    def decoded_user_parameters(self) -> Optional[Dict[str, Any]]:
        """Json Decoded action configuration user parameters"""
        return self.data.action_configuration.configuration.decoded_user_parameters

    @property
    def input_bucket_name(self) -> str:
        """Get the first input artifact bucket name"""
        return self.data.input_artifacts[0].location.s3_location.bucket_name

    @property
    def input_object_key(self) -> str:
        """Get the first input artifact order key unquote plus"""
        return self.data.input_artifacts[0].location.s3_location.object_key

    def setup_s3_client(self):
        """Creates an S3 client

        Uses the credentials passed in the event by CodePipeline. These
        credentials can be used to access the artifact bucket.

        Returns
        -------
        BaseClient
            An S3 client with the appropriate credentials
        """
        # IMPORTING boto3 within the FUNCTION and not at the top level to get
        # it only when we explicitly want it for better performance.
        import boto3

        from aws_lambda_powertools.shared import user_agent

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.data.artifact_credentials.access_key_id,
            aws_secret_access_key=self.data.artifact_credentials.secret_access_key,
            aws_session_token=self.data.artifact_credentials.session_token,
        )
        user_agent.register_feature_to_client(client=s3, feature="data_classes")
        return s3

    def find_input_artifact(self, artifact_name: str) -> Optional[CodePipelineArtifact]:
        """Find an input artifact by artifact name

        Parameters
        ----------
        artifact_name : str
            The name of the input artifact to look for

        Returns
        -------
        CodePipelineArtifact, None
            Matching CodePipelineArtifact if found
        """
        for artifact in self.data.input_artifacts:
            if artifact.name == artifact_name:
                return artifact
        return None

    def get_artifact(self, artifact_name: str, filename: str) -> Optional[str]:
        """Get a file within an artifact zip on s3

        Parameters
        ----------
        artifact_name : str
            Name of the S3 artifact to download
        filename : str
            The file name within the artifact zip to extract as a string

        Returns
        -------
        str, None
            Returns the contents file contents as a string
        """
        artifact = self.find_input_artifact(artifact_name)
        if artifact is None:
            return None

        with tempfile.NamedTemporaryFile() as tmp_file:
            s3 = self.setup_s3_client()
            bucket = artifact.location.s3_location.bucket_name
            key = artifact.location.s3_location.key
            s3.download_file(bucket, key, tmp_file.name)
            with zipfile.ZipFile(tmp_file.name, "r") as zip_file:
                return zip_file.read(filename).decode("UTF-8")

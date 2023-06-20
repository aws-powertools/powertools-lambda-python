import json
import zipfile

import pytest
from pytest_mock import MockerFixture

from aws_lambda_powertools.utilities.data_classes import CodePipelineJobEvent
from aws_lambda_powertools.utilities.data_classes.code_pipeline_job_event import (
    CodePipelineData,
)
from tests.functional.utils import load_event


def test_code_pipeline_event():
    event = CodePipelineJobEvent(load_event("codePipelineEvent.json"))

    job = event["CodePipeline.job"]
    assert job["id"] == event.get_id
    assert job["accountId"] == event.account_id

    data = event.data
    assert isinstance(data, CodePipelineData)
    assert job["data"]["continuationToken"] == data.continuation_token
    configuration = data.action_configuration.configuration
    assert "MyLambdaFunctionForAWSCodePipeline" == configuration.function_name
    assert event.user_parameters == configuration.user_parameters
    assert "some-input-such-as-a-URL" == configuration.user_parameters

    input_artifacts = data.input_artifacts
    assert len(input_artifacts) == 1
    assert "ArtifactName" == input_artifacts[0].name
    assert input_artifacts[0].revision is None
    assert "S3" == input_artifacts[0].location.get_type

    output_artifacts = data.output_artifacts
    assert len(output_artifacts) == 0

    artifact_credentials = data.artifact_credentials
    artifact_credentials_dict = event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert artifact_credentials_dict["accessKeyId"] == artifact_credentials.access_key_id
    assert artifact_credentials_dict["secretAccessKey"] == artifact_credentials.secret_access_key
    assert artifact_credentials_dict["sessionToken"] == artifact_credentials.session_token


def test_code_pipeline_event_with_encryption_keys():
    event = CodePipelineJobEvent(load_event("codePipelineEventWithEncryptionKey.json"))

    job = event["CodePipeline.job"]
    assert job["id"] == event.get_id
    assert job["accountId"] == event.account_id

    data = event.data
    assert isinstance(data, CodePipelineData)
    assert job["data"]["continuationToken"] == data.continuation_token
    configuration = data.action_configuration.configuration
    assert "MyLambdaFunctionForAWSCodePipeline" == configuration.function_name
    assert event.user_parameters == configuration.user_parameters
    assert "some-input-such-as-a-URL" == configuration.user_parameters

    input_artifacts = data.input_artifacts
    assert len(input_artifacts) == 1
    assert "ArtifactName" == input_artifacts[0].name
    assert input_artifacts[0].revision is None
    assert "S3" == input_artifacts[0].location.get_type

    output_artifacts = data.output_artifacts
    assert len(output_artifacts) == 0

    artifact_credentials = data.artifact_credentials
    artifact_credentials_dict = event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert artifact_credentials_dict["accessKeyId"] == artifact_credentials.access_key_id
    assert artifact_credentials_dict["secretAccessKey"] == artifact_credentials.secret_access_key
    assert artifact_credentials_dict["sessionToken"] == artifact_credentials.session_token

    encryption_key = data.encryption_key
    assert "arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab" == encryption_key.get_id
    assert "KMS" == encryption_key.get_type


def test_code_pipeline_event_missing_user_parameters():
    event = CodePipelineJobEvent(load_event("codePipelineEventEmptyUserParameters.json"))

    assert event.data.continuation_token is None
    configuration = event.data.action_configuration.configuration
    decoded_params = configuration.decoded_user_parameters
    assert decoded_params == event.decoded_user_parameters
    assert decoded_params is None
    assert configuration.decoded_user_parameters is None


def test_code_pipeline_event_non_json_user_parameters():
    event = CodePipelineJobEvent(load_event("codePipelineEvent.json"))

    configuration = event.data.action_configuration.configuration
    assert configuration.user_parameters is not None

    with pytest.raises(json.decoder.JSONDecodeError):
        configuration.decoded_user_parameters


def test_code_pipeline_event_decoded_data():
    event = CodePipelineJobEvent(load_event("codePipelineEventData.json"))

    assert event.data.continuation_token is None
    configuration = event.data.action_configuration.configuration
    decoded_params = configuration.decoded_user_parameters
    assert decoded_params == event.decoded_user_parameters
    assert decoded_params["KEY"] == "VALUE"
    assert configuration.decoded_user_parameters["KEY"] == "VALUE"

    assert "my-pipeline-SourceArtifact" == event.data.input_artifacts[0].name

    output_artifacts = event.data.output_artifacts
    assert len(output_artifacts) == 1
    assert "S3" == output_artifacts[0].location.get_type
    assert "my-pipeline/invokeOutp/D0YHsJn" == output_artifacts[0].location.s3_location.key

    artifact_credentials = event.data.artifact_credentials
    artifact_credentials_dict = event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert isinstance(artifact_credentials.expiration_time, int)
    assert artifact_credentials_dict["expirationTime"] == artifact_credentials.expiration_time

    assert "us-west-2-123456789012-my-pipeline" == event.input_bucket_name
    assert "my-pipeline/test-api-2/TdOSFRV" == event.input_object_key


def test_code_pipeline_get_artifact_not_found():
    event = CodePipelineJobEvent(load_event("codePipelineEventData.json"))

    assert event.find_input_artifact("not-found") is None
    assert event.get_artifact("not-found", "foo") is None


def test_code_pipeline_get_artifact(mocker: MockerFixture):
    filename = "foo.json"
    file_contents = "Foo"

    class MockClient:
        @staticmethod
        def download_file(bucket: str, key: str, tmp_name: str):
            assert bucket == "us-west-2-123456789012-my-pipeline"
            assert key == "my-pipeline/test-api-2/TdOSFRV"
            with zipfile.ZipFile(tmp_name, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(filename, file_contents)

    s3 = mocker.patch("boto3.client")
    s3.return_value = MockClient()

    event = CodePipelineJobEvent(load_event("codePipelineEventData.json"))

    artifact_str = event.get_artifact(artifact_name="my-pipeline-SourceArtifact", filename=filename)

    s3.assert_called_once_with(
        "s3",
        **{
            "aws_access_key_id": event.data.artifact_credentials.access_key_id,
            "aws_secret_access_key": event.data.artifact_credentials.secret_access_key,
            "aws_session_token": event.data.artifact_credentials.session_token,
        }
    )
    assert artifact_str == file_contents

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
    raw_event = load_event("codePipelineEvent.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    job = raw_event["CodePipeline.job"]
    assert job["id"] == parsed_event.get_id
    assert job["accountId"] == parsed_event.account_id

    data = parsed_event.data
    assert isinstance(data, CodePipelineData)
    assert data.continuation_token == job["data"]["continuationToken"]

    configuration = data.action_configuration.configuration
    configuration_raw = raw_event["CodePipeline.job"]["data"]["actionConfiguration"]["configuration"]
    assert configuration.function_name == configuration_raw["FunctionName"]
    assert parsed_event.user_parameters == configuration_raw["UserParameters"]
    assert configuration.user_parameters == configuration_raw["UserParameters"]

    input_artifacts = data.input_artifacts
    input_artifacts_raw = raw_event["CodePipeline.job"]["data"]["inputArtifacts"][0]
    assert len(input_artifacts) == 1
    assert input_artifacts[0].name == input_artifacts_raw["name"]
    assert input_artifacts[0].revision is None
    assert input_artifacts[0].location.get_type == input_artifacts_raw["location"]["type"]

    output_artifacts = data.output_artifacts
    assert len(output_artifacts) == 0

    artifact_credentials = data.artifact_credentials
    artifact_credentials_raw = raw_event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert artifact_credentials.access_key_id == artifact_credentials_raw["accessKeyId"]
    assert artifact_credentials.secret_access_key == artifact_credentials_raw["secretAccessKey"]
    assert artifact_credentials.session_token == artifact_credentials_raw["sessionToken"]


def test_code_pipeline_event_with_encryption_keys():
    raw_event = load_event("codePipelineEventWithEncryptionKey.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    job = raw_event["CodePipeline.job"]
    assert job["id"] == parsed_event.get_id
    assert job["accountId"] == parsed_event.account_id

    data = parsed_event.data
    assert isinstance(data, CodePipelineData)
    assert data.continuation_token == job["data"]["continuationToken"]

    configuration = data.action_configuration.configuration
    configuration_raw = raw_event["CodePipeline.job"]["data"]["actionConfiguration"]["configuration"]
    assert configuration.function_name == configuration_raw["FunctionName"]
    assert parsed_event.user_parameters == configuration_raw["UserParameters"]
    assert configuration.user_parameters == configuration_raw["UserParameters"]

    input_artifacts = data.input_artifacts
    input_artifacts_raw = raw_event["CodePipeline.job"]["data"]["inputArtifacts"][0]
    assert len(input_artifacts) == 1
    assert input_artifacts[0].name == input_artifacts_raw["name"]
    assert input_artifacts[0].revision is None
    assert input_artifacts[0].location.get_type == input_artifacts_raw["location"]["type"]

    output_artifacts = data.output_artifacts
    assert len(output_artifacts) == 0

    artifact_credentials = data.artifact_credentials
    artifact_credentials_raw = raw_event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert artifact_credentials.access_key_id == artifact_credentials_raw["accessKeyId"]
    assert artifact_credentials.secret_access_key == artifact_credentials_raw["secretAccessKey"]
    assert artifact_credentials.session_token == artifact_credentials_raw["sessionToken"]

    encryption_key = data.encryption_key
    assert encryption_key.get_id == raw_event["CodePipeline.job"]["data"]["encryptionKey"]["id"]
    assert encryption_key.get_type == raw_event["CodePipeline.job"]["data"]["encryptionKey"]["type"]


def test_code_pipeline_event_missing_user_parameters():
    raw_event = load_event("codePipelineEventEmptyUserParameters.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    assert parsed_event.data.continuation_token is None
    configuration = parsed_event.data.action_configuration.configuration
    decoded_params = configuration.decoded_user_parameters
    assert decoded_params == parsed_event.decoded_user_parameters
    assert decoded_params is None
    assert configuration.decoded_user_parameters is None


def test_code_pipeline_event_non_json_user_parameters():
    raw_event = load_event("codePipelineEvent.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    configuration = parsed_event.data.action_configuration.configuration
    assert configuration.user_parameters is not None

    with pytest.raises(json.decoder.JSONDecodeError):
        assert configuration.decoded_user_parameters is not None


def test_code_pipeline_event_decoded_data():
    raw_event = load_event("codePipelineEventData.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    assert parsed_event.data.continuation_token is None
    configuration = parsed_event.data.action_configuration.configuration
    decoded_params = configuration.decoded_user_parameters
    assert decoded_params == parsed_event.decoded_user_parameters
    assert decoded_params["KEY"] == "VALUE"
    assert configuration.decoded_user_parameters["KEY"] == "VALUE"

    assert (
        parsed_event.data.input_artifacts[0].name == raw_event["CodePipeline.job"]["data"]["inputArtifacts"][0]["name"]
    )
    output_artifacts = parsed_event.data.output_artifacts
    assert len(output_artifacts) == 1
    assert (
        output_artifacts[0].location.get_type
        == raw_event["CodePipeline.job"]["data"]["outputArtifacts"][0]["location"]["type"]
    )
    assert (
        output_artifacts[0].location.s3_location.key
        == raw_event["CodePipeline.job"]["data"]["outputArtifacts"][0]["location"]["s3Location"]["objectKey"]
    )

    artifact_credentials = parsed_event.data.artifact_credentials
    artifact_credentials_raw = raw_event["CodePipeline.job"]["data"]["artifactCredentials"]
    assert isinstance(artifact_credentials.expiration_time, int)
    assert artifact_credentials.expiration_time == artifact_credentials_raw["expirationTime"]

    assert (
        parsed_event.input_bucket_name
        == raw_event["CodePipeline.job"]["data"]["inputArtifacts"][0]["location"]["s3Location"]["bucketName"]
    )
    assert (
        parsed_event.input_object_key
        == raw_event["CodePipeline.job"]["data"]["inputArtifacts"][0]["location"]["s3Location"]["objectKey"]
    )


def test_code_pipeline_get_artifact_not_found():
    raw_event = load_event("codePipelineEventData.json")
    parsed_event = CodePipelineJobEvent(raw_event)

    assert parsed_event.find_input_artifact("not-found") is None
    assert parsed_event.get_artifact("not-found", "foo") is None


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
        },
    )
    assert artifact_str == file_contents

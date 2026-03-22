from unittest.mock import patch

from aws_lambda_powertools.utilities.metadata import LambdaMetadata, clear_metadata_cache, get_lambda_metadata


def test_handler_uses_metadata(monkeypatch):
    # GIVEN a Lambda environment with metadata env vars
    monkeypatch.setenv("AWS_LAMBDA_INITIALIZATION_TYPE", "on-demand")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_API", "127.0.0.1:1234")
    monkeypatch.setenv("AWS_LAMBDA_METADATA_TOKEN", "test-token")

    mock_response = {"AvailabilityZoneID": "use1-az1"}

    with patch(
        "aws_lambda_powertools.utilities.metadata.lambda_metadata._fetch_metadata",
        return_value=mock_response,
    ):
        # WHEN calling get_lambda_metadata
        metadata: LambdaMetadata = get_lambda_metadata()

        # THEN it returns the mocked metadata
        assert metadata.availability_zone_id == "use1-az1"

    # Clean up cache between tests
    clear_metadata_cache()


def test_handler_works_outside_lambda():
    # GIVEN no Lambda environment variables are set
    # WHEN calling get_lambda_metadata
    metadata: LambdaMetadata = get_lambda_metadata()

    # THEN it returns empty metadata without errors
    assert metadata.availability_zone_id is None

import pytest

from aws_lambda_powertools.utilities.data_classes.transfer_family_event import (
    TransferFamilyAuthorizer,
    TransferFamilyAuthorizerResponse,
)
from tests.functional.utils import load_event


def test_transfer_family_authorizer_event():
    raw_event = load_event("transferFamilyAuthorizer.json")
    parsed_event = TransferFamilyAuthorizer(raw_event)

    assert parsed_event.username == raw_event["username"]
    assert parsed_event.password == raw_event["password"]
    assert parsed_event.protocol == raw_event["protocol"]
    assert parsed_event.server_id == raw_event["serverId"]
    assert parsed_event.source_ip == raw_event["sourceIp"]


@pytest.mark.parametrize("home_directory_type", ["LOGICAL", "PATH"])
def test_build_authentication_response_s3(home_directory_type):

    # GIVEN a Authorizer response
    response = TransferFamilyAuthorizerResponse()

    role_arn = "arn:aws:iam::123456789012:role/S3Access"
    policy = '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}'
    home_directory = "/bucket/user" if home_directory_type == "PATH" else None
    home_directory_details = (
        {"Entry": "/", "Target": "/bucket/${transfer:UserName}"} if home_directory_type == "LOGICAL" else None
    )
    public_keys = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0g+Z"

    # WHEN building an authentication response for S3 with different home directory types
    response = response.build_authentication_response_s3(
        role_arn=role_arn,
        policy=policy,
        home_directory=home_directory,
        home_directory_details=home_directory_details,
        home_directory_type=home_directory_type,
        public_keys=public_keys,
    )

    # THEN the authentication response is correctly built
    assert isinstance(response, dict)
    assert response.get("Role") == role_arn
    assert response.get("Policy") == policy
    assert response.get("PublicKeys") == public_keys

    if home_directory_type == "PATH":
        assert response.get("HomeDirectory") == home_directory
        assert "HomeDirectoryDetails" not in response
    else:
        assert response.get("HomeDirectoryDetails") == [home_directory_details]
        assert "HomeDirectory" not in response


@pytest.mark.parametrize("home_directory_type", ["LOGICAL", "PATH"])
def test_build_authentication_response_efs(home_directory_type):

    # GIVEN a Authorizer response
    response = TransferFamilyAuthorizerResponse()

    role_arn = "arn:aws:iam::123456789012:role/S3Access"
    home_directory = "/bucket/user" if home_directory_type == "PATH" else None
    home_directory_details = (
        {"Entry": "/", "Target": "/bucket/${transfer:UserName}"} if home_directory_type == "LOGICAL" else None
    )

    # WHEN building an authentication response for EFS with different home directory types
    response = response.build_authentication_response_efs(
        role_arn=role_arn,
        home_directory=home_directory,
        home_directory_details=home_directory_details,
        home_directory_type=home_directory_type,
        user_gid=0,
        user_uid=0,
    )

    # THEN the authentication response is correctly built
    assert isinstance(response, dict)
    assert response.get("Role") == role_arn

    if home_directory_type == "PATH":
        assert response.get("HomeDirectory") == home_directory
        assert "HomeDirectoryDetails" not in response
    else:
        assert response.get("HomeDirectoryDetails") == [home_directory_details]
        assert "HomeDirectory" not in response


def test_build_authentication_missing_home_directory():

    # GIVEN a Authorizer response
    response = TransferFamilyAuthorizerResponse()

    # WHEN home_directory_details is empty and type is LOGICAL
    role_arn = "arn:aws:iam::123456789012:role/S3Access"
    home_directory_details = {}
    home_directory_type = "LOGICAL"

    # THEN must raise an exception
    with pytest.raises(ValueError):
        response = response.build_authentication_response_efs(
            role_arn=role_arn,
            home_directory_details=home_directory_details,
            home_directory_type=home_directory_type,
            user_gid=0,
            user_uid=0,
        )


def test_build_authentication_response_invalid_type():
    # GIVEN a Authorizer response
    response = TransferFamilyAuthorizerResponse()

    # WHEN set an invalid home_directory_type
    invalid_type = "INVALID"

    # THEN must raise an exception
    with pytest.raises(ValueError):
        response.build_authentication_response_s3(
            role_arn="arn:aws:iam::123456789012:role/S3Access",
            home_directory_type=invalid_type,
        )


def test_build_authentication_response_missing_required_params():
    # GIVEN a Authorizer response
    response = TransferFamilyAuthorizerResponse()

    # WHEN set a PATH without home_directory
    home_directory_type = "PATH"

    # THEN must raise an exception
    with pytest.raises(ValueError):
        response.build_authentication_response_s3(
            role_arn="arn:aws:iam::123456789012:role/S3Access",
            home_directory_type=home_directory_type,
            # Missing required home_directory for PATH type
        )

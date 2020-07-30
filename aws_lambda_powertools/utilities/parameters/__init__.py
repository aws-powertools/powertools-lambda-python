# -*- coding: utf-8 -*-

"""
Parameter retrieval and caching utility
"""

from typing import Optional, Union

import boto3

from .base import BaseProvider

__all__ = ["BaseProvider", "DynamoDBProvider", "SecretsProvider", "SSMProvider", "get_parameter", "get_secret"]


class SSMProvider(BaseProvider):
    """
    AWS Systems Manager Parameter Store Provider
    """

    client = None

    def __init__(
        self, region: Optional[str] = None,
    ):
        """
        Initialize the SSM Parameter Store client
        """

        if region:
            self.client = boto3.client("ssm", region_name=region)
        else:
            self.client = boto3.client("ssm")

        super().__init__()

    def _get(self, name: str) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store
        """

        return self.client.get_parameter(Name=name)["Parameter"]["Value"]


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider
    """

    client = None

    def __init__(self, region: Optional[str] = None):
        """
        Initialize the Secrets Manager client
        """

        if region:
            self.client = boto3.client("secretsmanager", region_name=region)
        else:
            self.client = boto3.client("secretsmanager")

        super().__init__()

    def _get(self, name: str) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store
        """

        return self.client.get_secret_value(SecretId=name)["SecretString"]


class DynamoDBProvider(BaseProvider):
    """
    Amazon DynamoDB Parameter Provider
    """

    table = None
    key_attr = None
    value_attr = None

    def __init__(
        self, table_name: str, key_attr: str = "id", value_attr: str = "value", region: Optional[str] = None,
    ):
        """
        Initialize the DynamoDB client
        """

        if region:
            self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)
        else:
            self.table = boto3.resource("dynamodb").Table(table_name)

        self.key_attr = key_attr
        self.value_attr = value_attr

        super().__init__()

    def _get(self, name: str) -> str:
        """
        Retrieve a parameter value from Amazon DynamoDB
        """

        return self.table.get_item(Key={self.key_attr: name})["Item"][self.value_attr]


# These providers will be dynamically initialized on first use of the helper functions
_DEFAULT_PROVIDERS = {}


def get_parameter(name: str, transform: Optional[str] = None) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in _DEFAULT_PROVIDERS:
        _DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return _DEFAULT_PROVIDERS["ssm"].get(name, transform=transform)


def get_secret(name: str, transform: Optional[str] = None) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager
    """

    # Only create the provider if this function is called at least once
    if "secrets" not in _DEFAULT_PROVIDERS:
        _DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return _DEFAULT_PROVIDERS["secrets"].get(name, transform=transform)

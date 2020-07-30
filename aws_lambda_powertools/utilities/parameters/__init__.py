# -*- coding: utf-8 -*-

"""
Parameter retrieval and caching utility
"""

from typing import Dict, Optional, Union

import boto3
from boto3.dynamodb.conditions import Key

from .base import BaseProvider, GetParameterError

__all__ = [
    "BaseProvider",
    "GetParameterError",
    "DynamoDBProvider",
    "SecretsProvider",
    "SSMProvider",
    "get_parameter",
    "get_parameters",
    "get_secret",
]


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

        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region

        self.client = boto3.client("ssm", **client_kwargs)

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store

        Parameters
        ----------
        name: str
            Parameter name
        decrypt: bool
            If the parameter value should be decrypted
        """

        # Load kwargs
        decrypt = kwargs.get("decrypt", False)

        return self.client.get_parameter(Name=name, WithDecryption=decrypt)["Parameter"]["Value"]

    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from AWS Systems Manager Parameter Store

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        decrypt: bool
            If the parameter values should be decrypted
        recursive: bool
            If this should retrieve the parameter values recursively or not
        """

        # Load kwargs
        decrypt = kwargs.get("decrypt", False)
        recursive = kwargs.get("recursive", False)

        response = self.client.get_parameters_by_path(Path=path, WithDecryption=decrypt, Recursive=recursive)
        parameters = response.get("Parameters", [])

        # Keep retrieving parameters
        while "NextToken" in response:
            response = self.client.get_parameters_by_path(
                Path=path, WithDecryption=decrypt, Recursive=recursive, NextToken=response["NextToken"]
            )
            parameters.extend(response.get("Parameters", []))

        retval = {}
        for parameter in parameters:

            # Standardize the parameter name
            # The parameter name returned by SSM will contained the full path.
            # However, for readability, we should return only the part after
            # the path.
            name = parameter["Name"]
            if name.startswith(path):
                name = name[len(path) :]
            name = name.lstrip("/")

            retval[name] = parameter["Value"]

        return retval


class SecretsProvider(BaseProvider):
    """
    AWS Secrets Manager Parameter Provider
    """

    client = None

    def __init__(self, region: Optional[str] = None):
        """
        Initialize the Secrets Manager client
        """

        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region

        self.client = boto3.client("secretsmanager", **client_kwargs)

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store
        """

        return self.client.get_secret_value(SecretId=name)["SecretString"]

    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieving multiple parameter values is not supported with AWS Secrets Manager
        """
        raise NotImplementedError()


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

        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region
        self.table = boto3.resource("dynamodb", **client_kwargs).Table(table_name)

        self.key_attr = key_attr
        self.value_attr = value_attr

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from Amazon DynamoDB
        """

        return self.table.get_item(Key={self.key_attr: name})["Item"][self.value_attr]

    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from Amazon DynamoDB

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        sort_attr: str
            Name of the DynamoDB table sort key (defaults to 'sk')
        """

        sort_attr = kwargs.get("sort_attr", "sk")

        response = self.table.query(KeyConditionExpression=Key(self.key_attr).eq(path))
        items = response.get("Items", [])

        # Keep querying while there are more items matching the partition key
        while "LastEvaluatedKey" in response:
            response = self.table.query(
                KeyConditionExpression=Key(self.key_attr).eq(path), ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        retval = {}
        for item in items:
            retval[item[sort_attr]] = item[self.value_attr]

        return retval


# These providers will be dynamically initialized on first use of the helper functions
_DEFAULT_PROVIDERS = {}


def get_parameter(name: str, transform: Optional[str] = None) -> Union[str, list, dict, bytes]:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in _DEFAULT_PROVIDERS:
        _DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return _DEFAULT_PROVIDERS["ssm"].get(name, transform=transform)


def get_parameters(
    path: str, transform: Optional[str] = None, recursive: bool = False, decrypt: bool = False
) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
    """
    Retrieve multiple parameter values from AWS Systems Manager (SSM) Parameter Store
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in _DEFAULT_PROVIDERS:
        _DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return _DEFAULT_PROVIDERS["ssm"].get_multiple(path, transform=transform, recursive=recursive, decrypt=decrypt)


def get_secret(name: str, transform: Optional[str] = None, decrypt: bool = False) -> Union[str, dict, bytes]:
    """
    Retrieve a parameter value from AWS Secrets Manager
    """

    # Only create the provider if this function is called at least once
    if "secrets" not in _DEFAULT_PROVIDERS:
        _DEFAULT_PROVIDERS["secrets"] = SecretsProvider()

    return _DEFAULT_PROVIDERS["secrets"].get(name, transform=transform, decrypt=decrypt)

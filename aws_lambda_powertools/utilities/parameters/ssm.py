"""
AWS SSM Parameter retrieval and caching utility
"""


from typing import Dict, Optional, Union

import boto3
from botocore.config import Config

from .base import DEFAULT_PROVIDERS, BaseProvider


class SSMProvider(BaseProvider):
    """
    AWS Systems Manager Parameter Store Provider
    """

    client = None

    def __init__(
        self, config: Optional[Config] = None,
    ):
        """
        Initialize the SSM Parameter Store client
        """

        config = config or Config()
        self.client = boto3.client("ssm", config=config)

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


def get_parameter(name: str, transform: Optional[str] = None) -> Union[str, list, dict, bytes]:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get(name, transform=transform)


def get_parameters(
    path: str, transform: Optional[str] = None, recursive: bool = False, decrypt: bool = False
) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
    """
    Retrieve multiple parameter values from AWS Systems Manager (SSM) Parameter Store
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get_multiple(path, transform=transform, recursive=recursive, decrypt=decrypt)

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

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization

    Example
    -------
    **Retrieves a parameter value from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> value = ssm_provider.get("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value from Systems Manager Parameter Store in another AWS region**

        >>> from botocore.config import Config
        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>>
        >>> config = Config(region_name="us-west-1")
        >>> ssm_provider = SSMProvider(config=config)
        >>>
        >>> value = ssm_provider.get("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves multiple parameter values from Systems Manager Parameter Store using a path prefix**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> values = ssm_provider.get_multiple("/my/path/prefix")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        /my/path/prefix/a   Parameter value a
        /my/path/prefix/b   Parameter value b
        /my/path/prefix/c   Parameter value c

    **Retrieves multiple parameter values from Systems Manager Parameter Store passing options to the SDK call**

        >>> from aws_lambda_powertools.utilities.parameters import SSMProvider
        >>> ssm_provider = SSMProvider()
        >>>
        >>> values = ssm_provider.get_multiple("/my/path/prefix", MaxResults=10)
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        /my/path/prefix/a   Parameter value a
        /my/path/prefix/b   Parameter value b
        /my/path/prefix/c   Parameter value c
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

    def _get(self, name: str, decrypt: bool = False, **sdk_options) -> str:
        """
        Retrieve a parameter value from AWS Systems Manager Parameter Store

        Parameters
        ----------
        name: str
            Parameter name
        decrypt: bool, optional
            If the parameter value should be decrypted
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Parameter Store get_parameter API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["Name"] = name
        sdk_options["WithDecryption"] = decrypt

        return self.client.get_parameter(**sdk_options)["Parameter"]["Value"]

    def _get_multiple(self, path: str, decrypt: bool = False, recursive: bool = False, **sdk_options) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from AWS Systems Manager Parameter Store

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        decrypt: bool, optional
            If the parameter values should be decrypted
        recursive: bool, optional
            If this should retrieve the parameter values recursively or not
        sdk_options: dict, optional
            Dictionary of options that will be passed to the Parameter Store get_parameters_by_path API call
        """

        # Explicit arguments will take precedence over keyword arguments
        sdk_options["Path"] = path
        sdk_options["WithDecryption"] = decrypt
        sdk_options["Recursive"] = recursive

        response = self.client.get_parameters_by_path(**sdk_options)
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


def get_parameter(name: str, transform: Optional[str] = None, **sdk_options) -> Union[str, list, dict, bytes]:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    name: str
        Name of the parameter
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Parameter Store get_parameter API call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Retrieves a parameter value from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> get_parameter("/my/parameter")

    **Retrieves a parameter value and decodes it using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> get_parameter("/my/parameter", transform='binary')
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get(name, transform=transform)


def get_parameters(
    path: str, transform: Optional[str] = None, recursive: bool = False, decrypt: bool = False, **sdk_options
) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
    """
    Retrieve multiple parameter values from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    path: str
        Path to retrieve the parameters
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    decrypt: bool, optional
        If the parameter values should be decrypted
    recursive: bool, optional
        If this should retrieve the parameter values recursively or not
    sdk_options: dict, optional
        Dictionary of options that will be passed to the Parameter Store get_parameters_by_path API call

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve parameter values for
        a given path.
    TransformParameterError
        When the parameter provider fails to transform a parameter value.

    Example
    -------
    **Retrieves parameter values from Systems Manager Parameter Store**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> get_parameters("/my/path/parameter")

    **Retrieves parameter values and decodes them using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> get_parameters("/my/path/parameter", transform='binary')
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get_multiple(path, transform=transform, recursive=recursive, decrypt=decrypt)

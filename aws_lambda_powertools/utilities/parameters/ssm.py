"""
AWS SSM Parameter retrieval and caching utility
"""


from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import boto3
from botocore.config import Config

from .base import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS, BaseProvider

if TYPE_CHECKING:
    from mypy_boto3_ssm import SSMClient


class SSMProvider(BaseProvider):
    """
    AWS Systems Manager Parameter Store Provider

    Parameters
    ----------
    config: botocore.config.Config, optional
        Botocore configuration to pass during client initialization
    boto3_session : boto3.session.Session, optional
            Boto3 session to create a boto3_client from
    boto3_client: SSMClient, optional
            Boto3 SSM Client to use, boto3_session will be ignored if both are provided

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

    client: Any = None

    def __init__(
        self,
        config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
        boto3_client: Optional["SSMClient"] = None,
    ):
        """
        Initialize the SSM Parameter Store client
        """

        super().__init__()

        self.client: "SSMClient" = self._build_boto3_client(
            service_name="ssm", client=boto3_client, session=boto3_session, config=config
        )

    # We break Liskov substitution principle due to differences in signatures of this method and superclass get method
    # We ignore mypy error, as changes to the signature here or in a superclass is a breaking change to users
    def get(  # type: ignore[override]
        self,
        name: str,
        max_age: int = DEFAULT_MAX_AGE_SECS,
        transform: Optional[str] = None,
        decrypt: bool = False,
        force_fetch: bool = False,
        **sdk_options
    ) -> Optional[Union[str, dict, bytes]]:
        """
        Retrieve a parameter value or return the cached value

        Parameters
        ----------
        name: str
            Parameter name
        max_age: int
            Maximum age of the cached value
        transform: str
            Optional transformation of the parameter value. Supported values
            are "json" for JSON strings and "binary" for base 64 encoded
            values.
        decrypt: bool, optional
            If the parameter value should be decrypted
        force_fetch: bool, optional
            Force update even before a cached item has expired, defaults to False
        sdk_options: dict, optional
            Arguments that will be passed directly to the underlying API call

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve a parameter value for
            a given name.
        TransformParameterError
            When the parameter provider fails to transform a parameter value.
        """

        # Add to `decrypt` sdk_options to we can have an explicit option for this
        sdk_options["decrypt"] = decrypt

        return super().get(name, max_age, transform, force_fetch, **sdk_options)

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

        parameters = {}
        for page in self.client.get_paginator("get_parameters_by_path").paginate(**sdk_options):
            for parameter in page.get("Parameters", []):
                # Standardize the parameter name
                # The parameter name returned by SSM will contained the full path.
                # However, for readability, we should return only the part after
                # the path.
                name = parameter["Name"]
                if name.startswith(path):
                    name = name[len(path) :]
                name = name.lstrip("/")

                parameters[name] = parameter["Value"]

        return parameters


def get_parameter(
    name: str,
    transform: Optional[str] = None,
    decrypt: bool = False,
    force_fetch: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    **sdk_options
) -> Union[str, list, dict, bytes]:
    """
    Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    name: str
        Name of the parameter
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    decrypt: bool, optional
        If the parameter values should be decrypted
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int
        Maximum age of the cached value
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
        >>> value = get_parameter("/my/parameter")
        >>>
        >>> print(value)
        My parameter value

    **Retrieves a parameter value and decodes it using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> value = get_parameter("/my/parameter", transform='binary')
        >>>
        >>> print(value)
        My parameter value
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    # Add to `decrypt` sdk_options to we can have an explicit option for this
    sdk_options["decrypt"] = decrypt

    return DEFAULT_PROVIDERS["ssm"].get(
        name, max_age=max_age, transform=transform, force_fetch=force_fetch, **sdk_options
    )


def get_parameters(
    path: str,
    transform: Optional[str] = None,
    recursive: bool = True,
    decrypt: bool = False,
    force_fetch: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_transform_error: bool = False,
    **sdk_options
) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
    """
    Retrieve multiple parameter values from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    path: str
        Path to retrieve the parameters
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    recursive: bool, optional
        If this should retrieve the parameter values recursively or not, defaults to True
    decrypt: bool, optional
        If the parameter values should be decrypted
    force_fetch: bool, optional
        Force update even before a cached item has expired, defaults to False
    max_age: int
        Maximum age of the cached value
    raise_on_transform_error: bool, optional
        Raises an exception if any transform fails, otherwise this will
        return a None value for each transform that failed
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
        >>> values = get_parameters("/my/path/prefix")
        >>>
        >>> for key, value in values.items():
        ...     print(key, value)
        /my/path/prefix/a   Parameter value a
        /my/path/prefix/b   Parameter value b
        /my/path/prefix/c   Parameter value c

    **Retrieves parameter values and decodes them using a Base64 decoder**

        >>> from aws_lambda_powertools.utilities.parameters import get_parameter
        >>>
        >>> values = get_parameters("/my/path/prefix", transform='binary')
    """

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    sdk_options["recursive"] = recursive
    sdk_options["decrypt"] = decrypt

    return DEFAULT_PROVIDERS["ssm"].get_multiple(
        path,
        max_age=max_age,
        transform=transform,
        raise_on_transform_error=raise_on_transform_error,
        force_fetch=force_fetch,
        **sdk_options
    )

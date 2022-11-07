"""
AWS SSM Parameter retrieval and caching utility
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, overload

import boto3
from botocore.config import Config
from typing_extensions import Literal

from aws_lambda_powertools.shared.functions import slice_dictionary

from .base import DEFAULT_MAX_AGE_SECS, DEFAULT_PROVIDERS, BaseProvider, transform_value
from .exceptions import GetParameterError
from .types import TransformOptions

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
    _MAX_GET_PARAMETERS_ITEM = 10

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
        transform: TransformOptions = None,
        decrypt: bool = False,
        force_fetch: bool = False,
        **sdk_options,
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
                # The parameter name returned by SSM will contain the full path.
                # However, for readability, we should return only the part after
                # the path.
                name = parameter["Name"]
                if name.startswith(path):
                    name = name[len(path) :]
                name = name.lstrip("/")

                parameters[name] = parameter["Value"]

        return parameters

    def get_parameters_by_name(
        self,
        parameters: Dict[str, Dict],
        transform: TransformOptions = None,
        decrypt: bool = False,
        max_age: int = DEFAULT_MAX_AGE_SECS,
        raise_on_error: bool = True,
    ) -> Dict[str, str] | Dict[str, bytes] | Dict[str, dict]:
        """
        Retrieve multiple parameter values by name from SSM or cache.

        It uses GetParameter if a param requires decryption, otherwise GetParameters.

        Parameters
        ----------
        parameters: List[Dict[str, Dict]]
            List of parameter names, and any optional overrides
        transform: str, optional
            Transforms the content from a JSON object ('json') or base64 binary string ('binary')
        decrypt: bool, optional
            If the parameter values should be decrypted
        max_age: int
            Maximum age of the cached value
        raise_on_error: bool
            Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve a parameter value for
            a given name.
        """
        response: Dict[str, Any] = {}

        batch_params, decrypt_params = self._split_batch_and_decrypt_parameters(parameters, transform, max_age, decrypt)
        decrypt_ret, decrypt_err = self._get_parameters_by_name_with_decrypt_option(decrypt_params, raise_on_error)
        batch_ret, batch_err = self._get_parameters_by_name_batch(batch_params, raise_on_error)

        response.update(**batch_ret, **decrypt_ret)
        if not raise_on_error:
            response["_errors"] = [*decrypt_err, *batch_err]

        return response

    def _get_parameters_by_name_with_decrypt_option(
        self, batch: Dict[str, Dict], raise_on_error: bool
    ) -> Tuple[Dict, List]:
        response: Dict[str, Any] = {}
        errors: List[str] = []

        # Decided for single-thread as it outperforms in 128M and 1G + reduce timeout risk
        # see: https://github.com/awslabs/aws-lambda-powertools-python/issues/1040#issuecomment-1299954613
        for parameter, options in batch.items():
            try:
                response[parameter] = self.get(
                    parameter, max_age=options["max_age"], transform=options["transform"], decrypt=options["decrypt"]
                )
            except GetParameterError:
                if raise_on_error:
                    raise
                errors.append(parameter)
                continue

        return response, errors

    def _get_parameters_by_name_batch(self, batch: Dict[str, Dict], raise_on_error: bool = True) -> Tuple[Dict, List]:
        errors: List[str] = []

        # Fetch each possible batch param from cache and return if entire batch is cached
        cached_params = self._get_parameters_by_name_from_cache(batch)
        if len(cached_params) == len(batch):
            return cached_params, errors

        # Slice batch by max permitted GetParameters call
        batch_ret, errors = self._get_parameters_by_name_in_chunks(
            batch=batch, cache=cached_params, raise_on_error=raise_on_error
        )

        return {**cached_params, **batch_ret}, errors

    def _get_parameters_by_name_from_cache(self, batch: Dict[str, Dict]) -> Dict[str, Any]:
        """Fetch each parameter from batch that hasn't been expired"""
        cache = {}
        for name, options in batch.items():
            cache_key = (name, options["transform"])
            if self.has_not_expired_in_cache(cache_key):
                cache[name] = self.store[cache_key].value

        return cache

    def _get_parameters_by_name_in_chunks(
        self, batch: Dict[str, Dict], cache: Dict[str, Any], raise_on_error: bool
    ) -> Tuple[Dict, List]:
        """Take out differences from cache and batch, slice it and fetch from SSM"""
        response: Dict[str, Any] = {}
        errors: List[str] = []

        diff = {key: value for key, value in batch.items() if key not in cache}

        for chunk in slice_dictionary(data=diff, chunk_size=self._MAX_GET_PARAMETERS_ITEM):
            response, possible_errors = self._get_parameters_by_name(parameters=chunk, raise_on_error=raise_on_error)
            response.update(response)
            errors.extend(possible_errors)

        return response, errors

    def _get_parameters_by_name(
        self, parameters: Dict[str, Dict], raise_on_error: bool = True
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Use SSM GetParameters to fetch parameters, hydrate cache, and handle partial failure

        Parameters
        ----------
        parameters : Dict[str, Dict]
            Parameters to fetch
        raise_on_error : bool, optional
            Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

        Returns
        -------
        Dict[str, Any]
            Retrieved parameters as key names and their values

        Raises
        ------
        GetParameterError
            When one or more parameters failed on fetching, and raise_on_error is enabled
        """
        ret = {}
        batch_errors: List[str] = []

        response = self.client.get_parameters(Names=list(parameters.keys()))
        failed_parameters = response["InvalidParameters"]
        if failed_parameters:
            if raise_on_error:
                raise GetParameterError(f"Failed to fetch parameters: {failed_parameters}")
            else:
                batch_errors = failed_parameters

        # Built up cache_key, hydrate cache, and return `{name:value}`
        for parameter in response["Parameters"]:
            name = parameter["Name"]
            value = parameter["Value"]
            options = parameters[name]
            transform = options.get("transform", "")

            # NOTE: If transform is set, we do it before caching to reduce number of operations
            if transform:
                value = transform_value(
                    key=name, value=value, transform=transform, raise_on_transform_error=raise_on_error
                )

            _cache_key = (name, options["transform"])
            self.add_to_cache(key=_cache_key, value=value, max_age=options["max_age"])

            ret[name] = value

        return ret, batch_errors

    @staticmethod
    def _split_batch_and_decrypt_parameters(
        parameters: Dict[str, Dict], transform: TransformOptions, max_age: int, decrypt: bool
    ) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
        """Split parameters that can be fetched by GetParameters vs GetParameter

        Parameters
        ----------
        parameters : Dict[str, Dict]
            Parameters containing names as key and optional config override as value
        transform : TransformOptions
            Transform configuration
        max_age : int
            How long to cache a parameter for
        decrypt : bool
            Whether to use KMS to decrypt a parameter

        Returns
        -------
        Tuple[Dict[str, Dict], Dict[str, Dict]]
            GetParameters and GetParameter parameters dict along with their overrides/globals merged
        """
        batch_parameters: Dict[str, Dict] = {}
        decrypt_parameters: Dict[str, Any] = {}

        for parameter, options in parameters.items():
            # NOTE: TypeDict later
            _overrides = options or {}
            _overrides["transform"] = _overrides.get("transform") or transform

            # These values can be falsy (False, 0)
            if "decrypt" not in _overrides:
                _overrides["decrypt"] = decrypt

            if "max_age" not in _overrides:
                _overrides["max_age"] = max_age

            # NOTE: Split parameters who have decrypt OR have it global
            if _overrides["decrypt"]:
                decrypt_parameters[parameter] = _overrides
            else:
                batch_parameters[parameter] = _overrides

        return batch_parameters, decrypt_parameters


def get_parameter(
    name: str,
    transform: Optional[str] = None,
    decrypt: bool = False,
    force_fetch: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    **sdk_options,
) -> Union[str, dict, bytes]:
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
    **sdk_options,
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
        **sdk_options,
    )


@overload
def get_parameters_by_name(
    parameters: Dict[str, Dict],
    transform: None = None,
    decrypt: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_error: bool = True,
) -> Dict[str, str]:
    ...


@overload
def get_parameters_by_name(
    parameters: Dict[str, Dict],
    transform: Literal["binary"],
    decrypt: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_error: bool = True,
) -> Dict[str, bytes]:
    ...


@overload
def get_parameters_by_name(
    parameters: Dict[str, Dict],
    transform: Literal["json"],
    decrypt: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_error: bool = True,
) -> Dict[str, Dict[str, Any]]:
    ...


@overload
def get_parameters_by_name(
    parameters: Dict[str, Dict],
    transform: Literal["auto"],
    decrypt: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_error: bool = True,
) -> Union[Dict[str, str], Dict[str, dict]]:
    ...


def get_parameters_by_name(
    parameters: Dict[str, Any],
    transform: TransformOptions = None,
    decrypt: bool = False,
    max_age: int = DEFAULT_MAX_AGE_SECS,
    raise_on_error: bool = True,
) -> Union[Dict[str, str], Dict[str, bytes], Dict[str, dict]]:
    """
    Retrieve multiple parameter values by name from AWS Systems Manager (SSM) Parameter Store

    Parameters
    ----------
    parameters: List[Dict[str, Dict]]
        List of parameter names, and any optional overrides
    transform: str, optional
        Transforms the content from a JSON object ('json') or base64 binary string ('binary')
    decrypt: bool, optional
        If the parameter values should be decrypted
    max_age: int
        Maximum age of the cached value
    raise_on_error: bool, optional
        Whether to fail-fast or fail gracefully by including "_errors" key in the response, by default True

    Example
    -------

    **Retrieves multiple parameters from distinct paths from Systems Manager Parameter Store**

        from aws_lambda_powertools.utilities.parameters import get_parameters_by_name

        params = {
            "/param": {},
            "/json": {"transform": "json"},
            "/binary": {"transform": "binary"},
            "/no_cache": {"max_age": 0},
            "/api_key": {"decrypt": True},
        }

        values = get_parameters_by_name(parameters=params)
        for param_name, value in values.items():
            print(f"{param_name}: {value}")

        # "/param": value
        # "/json": value
        # "/binary": value
        # "/no_cache": value
        # "/api_key": value

    Raises
    ------
    GetParameterError
        When the parameter provider fails to retrieve a parameter value for
        a given name.
    """

    # NOTE: Decided against using multi-thread due to single-thread outperforming in 128M and 1G + timeout risk
    # see: https://github.com/awslabs/aws-lambda-powertools-python/issues/1040#issuecomment-1299954613

    # Only create the provider if this function is called at least once
    if "ssm" not in DEFAULT_PROVIDERS:
        DEFAULT_PROVIDERS["ssm"] = SSMProvider()

    return DEFAULT_PROVIDERS["ssm"].get_parameters_by_name(
        parameters=parameters, max_age=max_age, transform=transform, decrypt=decrypt, raise_on_error=raise_on_error
    )

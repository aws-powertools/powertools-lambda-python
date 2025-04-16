"""
Base for Parameter providers
!!! abstract "Usage Documentation"
    [`Parameters`](../../utilities/parameters.md)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, NamedTuple, cast, overload

from aws_lambda_powertools.shared import constants, user_agent
from aws_lambda_powertools.shared.functions import resolve_max_age
from aws_lambda_powertools.utilities.parameters.exceptions import GetParameterError, TransformParameterError

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.parameters.types import TransformOptions


from aws_lambda_powertools.utilities.parameters.constants import (
    DEFAULT_MAX_AGE_SECS,
    DEFAULT_PROVIDERS,
    TRANSFORM_METHOD_MAPPING,
)


class ExpirableValue(NamedTuple):
    value: str | bytes | dict[str, Any]
    ttl: datetime


class BaseProvider(ABC):
    """
    Abstract Base Class for Parameter providers
    """

    store: dict[tuple, ExpirableValue]

    def __init__(self, *, client=None, resource=None):
        """
        Initialize the base provider
        """
        if client is not None:
            user_agent.register_feature_to_client(client=client, feature="parameters")
        if resource is not None:
            user_agent.register_feature_to_resource(resource=resource, feature="parameters")

        self.store: dict[tuple, ExpirableValue] = {}

    def has_not_expired_in_cache(self, key: tuple) -> bool:
        return key in self.store and self.store[key].ttl >= datetime.now()

    def get(
        self,
        name: str,
        max_age: int | None = None,
        transform: TransformOptions = None,
        force_fetch: bool = False,
        **sdk_options,
    ) -> str | bytes | dict | None:
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

        # If there are multiple calls to the same parameter but in a different
        # transform, they will be stored multiple times. This allows us to
        # optimize by transforming the data only once per retrieval, thus there
        # is no need to transform cached values multiple times. However, this
        # means that we need to make multiple calls to the underlying parameter
        # store if we need to return it in different transforms. Since the number
        # of supported transform is small and the probability that a given
        # parameter will always be used in a specific transform, this should be
        # an acceptable tradeoff.
        value: str | bytes | dict | None = None
        key = self._build_cache_key(name=name, transform=transform)

        # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
        max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age)

        if not force_fetch and self.has_not_expired_in_cache(key):
            return self.fetch_from_cache(key)

        try:
            value = self._get(name, **sdk_options)
        # Encapsulate all errors into a generic GetParameterError
        except Exception as exc:
            raise GetParameterError(str(exc))

        if transform:
            value = transform_value(key=name, value=value, transform=transform, raise_on_transform_error=True)

        # NOTE: don't cache None, as they might've been failed transforms and may be corrected
        if value is not None:
            self.add_to_cache(key=key, value=value, max_age=max_age)

        return value

    @abstractmethod
    def _get(self, name: str, **sdk_options) -> str | bytes | dict[str, Any]:
        """
        Retrieve parameter value from the underlying parameter store
        """
        raise NotImplementedError()

    def set(self, name: str, value: Any, *, overwrite: bool = False, **kwargs):
        """
        Set parameter value from the underlying parameter store
        """
        raise NotImplementedError()

    def get_multiple(
        self,
        path: str,
        max_age: int | None = None,
        transform: TransformOptions = None,
        raise_on_transform_error: bool = False,
        force_fetch: bool = False,
        **sdk_options,
    ) -> dict[str, str] | dict[str, bytes] | dict[str, dict]:
        """
        Retrieve multiple parameters based on a path prefix

        Parameters
        ----------
        path: str
            Parameter path used to retrieve multiple parameters
        max_age: int, optional
            Maximum age of the cached value
        transform: str, optional
            Optional transformation of the parameter value. Supported values
            are "json" for JSON strings, "binary" for base 64 encoded
            values or "auto" which looks at the attribute key to determine the type.
        raise_on_transform_error: bool, optional
            Raises an exception if any transform fails, otherwise this will
            return a None value for each transform that failed
        force_fetch: bool, optional
            Force update even before a cached item has expired, defaults to False
        sdk_options: dict, optional
            Arguments that will be passed directly to the underlying API call

        Raises
        ------
        GetParameterError
            When the parameter provider fails to retrieve parameter values for
            a given path.
        TransformParameterError
            When the parameter provider fails to transform a parameter value.
        """
        key = self._build_cache_key(name=path, transform=transform, is_nested=True)

        # If max_age is not set, resolve it from the environment variable, defaulting to DEFAULT_MAX_AGE_SECS
        max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=max_age)

        if not force_fetch and self.has_not_expired_in_cache(key):
            return self.fetch_from_cache(key)

        try:
            values = self._get_multiple(path, **sdk_options)
        # Encapsulate all errors into a generic GetParameterError
        except Exception as exc:
            raise GetParameterError(str(exc))

        if transform:
            values.update(transform_value(values, transform, raise_on_transform_error))

        self.add_to_cache(key=key, value=values, max_age=max_age)

        return values

    @abstractmethod
    def _get_multiple(self, path: str, **sdk_options) -> dict[str, str]:
        """
        Retrieve multiple parameter values from the underlying parameter store
        """
        raise NotImplementedError()

    def clear_cache(self):
        self.store.clear()

    def fetch_from_cache(self, key: tuple):
        return self.store[key].value if key in self.store else {}

    def add_to_cache(self, key: tuple, value: Any, max_age: int):
        if max_age <= 0:
            return

        self.store[key] = ExpirableValue(value, datetime.now() + timedelta(seconds=max_age))

    def _build_cache_key(
        self,
        name: str,
        transform: TransformOptions = None,
        is_nested: bool = False,
    ):
        """Creates cache key for parameters

        Parameters
        ----------
        name : str
            Name of parameter, secret or config
        transform : TransformOptions, optional
            Transform method used, by default None
        is_nested : bool, optional
            Whether it's a single parameter or multiple nested parameters, by default False

        Returns
        -------
        tuple[str, TransformOptions, bool]
            Cache key
        """
        return (name, transform, is_nested)


def get_transform_method(value: str, transform: TransformOptions = None) -> Callable[..., Any]:
    """
    Determine the transform method

    Examples
    -------
        >>> get_transform_method("key","any_other_value")
        'any_other_value'
        >>> get_transform_method("key.json","auto")
        'json'
        >>> get_transform_method("key.binary","auto")
        'binary'
        >>> get_transform_method("key","auto")
        None
        >>> get_transform_method("key",None)
        None

    Parameters
    ---------
    value: str
        Only used when the transform is "auto".
    transform: str, optional
        Original transform method, only "auto" will try to detect the transform method by the key

    Returns
    ------
    Callable:
        Transform function could be json.loads, base64.b64decode, or a lambda that echo the str value
    """
    transform_method = TRANSFORM_METHOD_MAPPING.get(transform)

    if transform == "auto":
        key_suffix = value.rsplit(".")[-1]
        transform_method = TRANSFORM_METHOD_MAPPING.get(key_suffix, TRANSFORM_METHOD_MAPPING[None])

    return cast(Callable, transform_method)  # https://github.com/python/mypy/issues/10740


@overload
def transform_value(
    value: dict[str, Any],
    transform: TransformOptions,
    raise_on_transform_error: bool = False,
    key: str = "",
) -> dict[str, Any]: ...


@overload
def transform_value(
    value: str | bytes | dict[str, Any],
    transform: TransformOptions,
    raise_on_transform_error: bool = False,
    key: str = "",
) -> str | bytes | dict[str, Any] | None: ...


def transform_value(
    value: str | bytes | dict[str, Any],
    transform: TransformOptions,
    raise_on_transform_error: bool = True,
    key: str = "",
) -> str | bytes | dict[str, Any] | None:
    """
    Transform a value using one of the available options.

    Parameters
    ---------
    value: str
        Parameter value to transform
    transform: str
        Type of transform, supported values are "json", "binary", and "auto" based on suffix (.json, .binary)
    key: str
        Parameter key when transform is auto to infer its transform method
    raise_on_transform_error: bool, optional
        Raises an exception if any transform fails, otherwise this will
        return a None value for each transform that failed

    Raises
    ------
    TransformParameterError:
        When the parameter value could not be transformed
    """
    # Maintenance: For v3, we should consider returning the original value for soft transform failures.

    err_msg = "Unable to transform value using '{transform}' transform: {exc}"

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if isinstance(value, dict):
        # NOTE: We must handle partial failures when receiving multiple values
        # where one of the keys might fail during transform, e.g. `{"a": "valid", "b": "{"}`
        # expected: `{"a": "valid", "b": None}`

        transformed_values: dict[str, Any] = {}
        for dict_key, dict_value in value.items():
            transform_method = get_transform_method(value=dict_key, transform=transform)
            try:
                transformed_values[dict_key] = transform_method(dict_value)
            except Exception as exc:
                if raise_on_transform_error:
                    raise TransformParameterError(err_msg.format(transform=transform, exc=exc)) from exc
                transformed_values[dict_key] = None
        return transformed_values

    if transform == "auto":
        # key="a.json", value='{"a": "b"}', or key="a.binary", value="b64_encoded"
        transform_method = get_transform_method(value=key, transform=transform)
    else:
        # value='{"key": "value"}
        transform_method = get_transform_method(value=value, transform=transform)

    try:
        return transform_method(value)
    except Exception as exc:
        if raise_on_transform_error:
            raise TransformParameterError(err_msg.format(transform=transform, exc=exc)) from exc
        return None


def clear_caches():
    """Clear cached parameter values from all providers"""
    DEFAULT_PROVIDERS.clear()

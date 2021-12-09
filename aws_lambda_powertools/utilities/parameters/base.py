"""
Base for Parameter providers
"""

import base64
import json
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union

from .exceptions import GetParameterError, TransformParameterError

DEFAULT_MAX_AGE_SECS = 5
ExpirableValue = namedtuple("ExpirableValue", ["value", "ttl"])
# These providers will be dynamically initialized on first use of the helper functions
DEFAULT_PROVIDERS: Dict[str, Any] = {}
TRANSFORM_METHOD_JSON = "json"
TRANSFORM_METHOD_BINARY = "binary"
SUPPORTED_TRANSFORM_METHODS = [TRANSFORM_METHOD_JSON, TRANSFORM_METHOD_BINARY]


class BaseProvider(ABC):
    """
    Abstract Base Class for Parameter providers
    """

    store: Any = None

    def __init__(self):
        """
        Initialize the base provider
        """

        self.store = {}

    def _has_not_expired(self, key: Tuple[str, Optional[str]]) -> bool:
        return key in self.store and self.store[key].ttl >= datetime.now()

    def get(
        self,
        name: str,
        max_age: int = DEFAULT_MAX_AGE_SECS,
        transform: Optional[str] = None,
        force_fetch: bool = False,
        **sdk_options,
    ) -> Union[str, list, dict, bytes]:
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
        key = (name, transform)

        if not force_fetch and self._has_not_expired(key):
            return self.store[key].value

        try:
            value = self._get(name, **sdk_options)
        # Encapsulate all errors into a generic GetParameterError
        except Exception as exc:
            raise GetParameterError(str(exc))

        if transform is not None:
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            value = transform_value(value, transform)

        self.store[key] = ExpirableValue(value, datetime.now() + timedelta(seconds=max_age))

        return value

    @abstractmethod
    def _get(self, name: str, **sdk_options) -> Union[str, bytes]:
        """
        Retrieve parameter value from the underlying parameter store
        """
        raise NotImplementedError()

    def get_multiple(
        self,
        path: str,
        max_age: int = DEFAULT_MAX_AGE_SECS,
        transform: Optional[str] = None,
        raise_on_transform_error: bool = False,
        force_fetch: bool = False,
        **sdk_options,
    ) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
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

        key = (path, transform)

        if not force_fetch and self._has_not_expired(key):
            return self.store[key].value

        try:
            values: Dict[str, Union[str, bytes, dict, None]] = self._get_multiple(path, **sdk_options)
        # Encapsulate all errors into a generic GetParameterError
        except Exception as exc:
            raise GetParameterError(str(exc))

        if transform is not None:
            for (key, value) in values.items():
                _transform = get_transform_method(key, transform)
                if _transform is None:
                    continue

                values[key] = transform_value(value, _transform, raise_on_transform_error)

        self.store[key] = ExpirableValue(values, datetime.now() + timedelta(seconds=max_age))

        return values

    @abstractmethod
    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from the underlying parameter store
        """
        raise NotImplementedError()


def get_transform_method(key: str, transform: Optional[str] = None) -> Optional[str]:
    """
    Determine the transform method

    Examples
    -------
        >>> get_transform_method("key", "any_other_value")
        'any_other_value'
        >>> get_transform_method("key.json", "auto")
        'json'
        >>> get_transform_method("key.binary", "auto")
        'binary'
        >>> get_transform_method("key", "auto")
        None
        >>> get_transform_method("key", None)
        None

    Parameters
    ---------
    key: str
        Only used when the tranform is "auto".
    transform: str, optional
        Original transform method, only "auto" will try to detect the transform method by the key

    Returns
    ------
    Optional[str]:
        The transform method either when transform is "auto" then None, "json" or "binary" is returned
        or the original transform method
    """
    if transform != "auto":
        return transform

    for transform_method in SUPPORTED_TRANSFORM_METHODS:
        if key.endswith("." + transform_method):
            return transform_method
    return None


def transform_value(value: str, transform: str, raise_on_transform_error: bool = True) -> Union[dict, bytes, None]:
    """
    Apply a transform to a value

    Parameters
    ---------
    value: str
        Parameter value to transform
    transform: str
        Type of transform, supported values are "json" and "binary"
    raise_on_transform_error: bool, optional
        Raises an exception if any transform fails, otherwise this will
        return a None value for each transform that failed

    Raises
    ------
    TransformParameterError:
        When the parameter value could not be transformed
    """

    try:
        if transform == TRANSFORM_METHOD_JSON:
            return json.loads(value)
        elif transform == TRANSFORM_METHOD_BINARY:
            return base64.b64decode(value)
        else:
            raise ValueError(f"Invalid transform type '{transform}'")

    except Exception as exc:
        if raise_on_transform_error:
            raise TransformParameterError(str(exc))
        return None

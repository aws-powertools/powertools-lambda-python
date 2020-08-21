"""
Base for Parameter providers
"""

import base64
import json
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from .exceptions import GetParameterError, TransformParameterError

DEFAULT_MAX_AGE_SECS = 5
ExpirableValue = namedtuple("ExpirableValue", ["value", "ttl"])
# These providers will be dynamically initialized on first use of the helper functions
DEFAULT_PROVIDERS = {}


class BaseProvider(ABC):
    """
    Abstract Base Class for Parameter providers
    """

    store = None

    def __init__(self):
        """
        Initialize the base provider
        """

        self.store = {}

    def get(
        self, name: str, max_age: int = DEFAULT_MAX_AGE_SECS, transform: Optional[str] = None, **sdk_options
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

        if key not in self.store or self.store[key].ttl < datetime.now():
            try:
                value = self._get(name, **sdk_options)
            # Encapsulate all errors into a generic GetParameterError
            except Exception as exc:
                raise GetParameterError(str(exc))

            if transform is not None:
                value = transform_value(value, transform)

            self.store[key] = ExpirableValue(value, datetime.now() + timedelta(seconds=max_age),)

        return self.store[key].value

    @abstractmethod
    def _get(self, name: str, **sdk_options) -> str:
        """
        Retrieve paramater value from the underlying parameter store
        """
        raise NotImplementedError()

    def get_multiple(
        self,
        path: str,
        max_age: int = DEFAULT_MAX_AGE_SECS,
        transform: Optional[str] = None,
        raise_on_transform_error: bool = False,
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
            are "json" for JSON strings and "binary" for base 64 encoded
            values.
        raise_on_transform_error: bool, optional
            Raises an exception if any transform fails, otherwise this will
            return a None value for each transform that failed
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

        if key not in self.store or self.store[key].ttl < datetime.now():
            try:
                values = self._get_multiple(path, **sdk_options)
            # Encapsulate all errors into a generic GetParameterError
            except Exception as exc:
                raise GetParameterError(str(exc))

            if transform is not None:
                new_values = {}
                for key, value in values.items():
                    try:
                        new_values[key] = transform_value(value, transform)
                    except Exception as exc:
                        if raise_on_transform_error:
                            raise exc
                        else:
                            new_values[key] = None

                values = new_values

            self.store[key] = ExpirableValue(values, datetime.now() + timedelta(seconds=max_age),)

        return self.store[key].value

    @abstractmethod
    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from the underlying parameter store
        """
        raise NotImplementedError()


def transform_value(value: str, transform: str) -> Union[dict, bytes]:
    """
    Apply a transform to a value

    Parameters
    ---------
    value: str
        Parameter alue to transform
    transform: str
        Type of transform, supported values are "json" and "binary"

    Raises
    ------
    TransformParameterError:
        When the parameter value could not be transformed
    """

    try:
        if transform == "json":
            return json.loads(value)
        elif transform == "binary":
            return base64.b64decode(value)
        else:
            raise ValueError(f"Invalid transform type '{transform}'")

    except Exception as exc:
        raise TransformParameterError(str(exc))

"""
Base for Parameter providers
"""

import base64
import json
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

DEFAULT_MAX_AGE_SECS = 5
ExpirableValue = namedtuple("ExpirableValue", ["value", "ttl"])


class GetParameterError(Exception):
    """When a provider raises an exception on parameter retrieval"""


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
        self, name: str, max_age: int = DEFAULT_MAX_AGE_SECS, transform: Optional[str] = None, **kwargs
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

        Raises
        ------

        GetParameterError
            When the parameter provider fails to retrieve a parameter value for
            a given name.
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
                value = self._get(name, **kwargs)
            # Encapsulate all errors into a generic GetParameterError
            except Exception as exc:
                raise GetParameterError(str(exc))

            if transform == "json":
                value = json.loads(value)
            elif transform == "binary":
                value = base64.b64decode(value)

            self.store[key] = ExpirableValue(value, datetime.now() + timedelta(seconds=max_age),)

        return self.store[key].value

    @abstractmethod
    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve paramater value from the underlying parameter store
        """
        raise NotImplementedError()

    def get_multiple(
        self, path: str, max_age: int = DEFAULT_MAX_AGE_SECS, transform: Optional[str] = None, **kwargs
    ) -> Union[Dict[str, str], Dict[str, dict], Dict[str, bytes]]:
        """
        Retrieve multiple parameters based on a path prefix
        """

        key = (path, transform)

        if key not in self.store or self.store[key].ttl < datetime.now():
            try:
                values = self._get_multiple(path, **kwargs)
            # Encapsulate all errors into a generic GetParameterError
            except Exception as exc:
                raise GetParameterError(str(exc))

            if transform == "json":
                values = {k: json.loads(v) for k, v in values}
            elif transform == "binary":
                values = {k: base64.b64decode(v) for k, v in values}

            self.store[key] = ExpirableValue(values, datetime.now() + timedelta(seconds=max_age),)

        return self.store[key].value

    @abstractmethod
    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from the underlying parameter store
        """
        raise NotImplementedError()

"""
Built-in JMESPath Functions to easily deserialize common encoded JSON payloads in Lambda functions.
!!! abstract "Usage Documentation"
    [`JMESPath Functions`](../utilities/jmespath_functions.md)
"""

from __future__ import annotations

import base64
import gzip
import json
import logging
import warnings
from typing import Any

import jmespath
from jmespath.exceptions import LexerError
from jmespath.functions import Functions, signature
from typing_extensions import deprecated

from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError
from aws_lambda_powertools.warnings import PowertoolsDeprecationWarning

logger = logging.getLogger(__name__)


class PowertoolsFunctions(Functions):
    @signature({"types": ["string"]})
    def _func_powertools_json(self, value):
        return json.loads(value)

    @signature({"types": ["string"]})
    def _func_powertools_base64(self, value):
        return base64.b64decode(value).decode()

    @signature({"types": ["string"]})
    def _func_powertools_base64_gzip(self, value):
        encoded = base64.b64decode(value)
        uncompressed = gzip.decompress(encoded)

        return uncompressed.decode()


def query(data: dict | str, envelope: str, jmespath_options: dict | None = None) -> Any:
    """Searches and extracts data using JMESPath

    Envelope being the JMESPath expression to extract the data you're after

    Built-in JMESPath functions include: powertools_json, powertools_base64, powertools_base64_gzip

    Example
    --------

    **Deserialize JSON string and extracts data from body key**

        from aws_lambda_powertools.utilities.jmespath_utils import query
        from aws_lambda_powertools.utilities.typing import LambdaContext


        def handler(event: dict, context: LambdaContext):
            # event = {"body": "{\"customerId\":\"dd4649e6-2484-4993-acb8-0f9123103394\"}"}  # noqa: ERA001
            payload = query(data=event, envelope="powertools_json(body)")
            customer = payload.get("customerId")  # now deserialized
            ...

    Parameters
    ----------
    data : dict | str
        Data set to be filtered
    envelope : str
        JMESPath expression to filter data against
    jmespath_options : dict | None
        Alternative JMESPath options to be included when filtering expr


    Returns
    -------
    Any
        Data found using JMESPath expression given in envelope
    """
    if not jmespath_options:
        jmespath_options = {"custom_functions": PowertoolsFunctions()}

    try:
        logger.debug(f"Envelope detected: {envelope}. JMESPath options: {jmespath_options}")
        return jmespath.search(envelope, data, options=jmespath.Options(**jmespath_options))
    except (LexerError, TypeError, UnicodeError) as e:
        message = f"Failed to unwrap event from envelope using expression. Error: {e} Exp: {envelope}, Data: {data}"  # noqa: B306, E501
        raise InvalidEnvelopeExpressionError(message)


@deprecated("`extract_data_from_envelope` is deprecated; use `query` instead.", category=None)
def extract_data_from_envelope(data: dict | str, envelope: str, jmespath_options: dict | None = None) -> Any:
    """Searches and extracts data using JMESPath

    *Deprecated*: Use query instead
    """
    warnings.warn(
        "The extract_data_from_envelope method is deprecated in V3 "
        "and will be removed in the next major version. Use query instead.",
        category=PowertoolsDeprecationWarning,
        stacklevel=2,
    )

    return query(data=data, envelope=envelope, jmespath_options=jmespath_options)

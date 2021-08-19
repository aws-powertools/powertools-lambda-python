import base64
import gzip
import json
import logging
from typing import Any, Dict, Optional, Union

import jmespath
from jmespath.exceptions import LexerError

from aws_lambda_powertools.exceptions import InvalidEnvelopeExpressionError

logger = logging.getLogger(__name__)


class PowertoolsFunctions(jmespath.functions.Functions):
    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_json(self, value):
        return json.loads(value)

    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_base64(self, value):
        return base64.b64decode(value).decode()

    @jmespath.functions.signature({"types": ["string"]})
    def _func_powertools_base64_gzip(self, value):
        encoded = base64.b64decode(value)
        uncompressed = gzip.decompress(encoded)

        return uncompressed.decode()


def extract_data_from_envelope(data: Union[Dict, str], envelope: str, jmespath_options: Optional[Dict]) -> Any:
    """Searches data using JMESPath expression

    Parameters
    ----------
    data : Dict
        Data set to be filtered
    envelope : str
        JMESPath expression to filter data against
    jmespath_options : Dict
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

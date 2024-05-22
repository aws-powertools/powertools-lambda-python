from typing import Any, Dict

from aws_lambda_powertools.utilities.data_classes.shared_functions import get_header_value


class _FrozenDict(dict):
    """
    A dictionary that can be used as a key in another dictionary.

    This is needed because the default dict implementation is not hashable.
    The only usage for this right now is to store dicts as part of the Router key.
    The implementation only takes into consideration the keys of the dictionary.

    MAINTENANCE: this is a temporary solution until we refactor the route key into a class.
    """

    def __hash__(self):
        return hash(frozenset(self.keys()))


def extract_origin_header(resolver_headers: Dict[str, Any]):
    """
    Extracts the 'origin' or 'Origin' header from the provided resolver headers.

    The 'origin' or 'Origin' header can be either a single header or a multi-header.

    Args:
        resolver_headers (Dict): A dictionary containing the headers.

    Returns:
        Optional[str]: The value(s) of the origin header or None.
    """
    resolved_header = get_header_value(resolver_headers, "origin", None, case_sensitive=False)
    if isinstance(resolved_header, str):
        return resolved_header
    if isinstance(resolved_header, list):
        return resolved_header[0]

    return resolved_header

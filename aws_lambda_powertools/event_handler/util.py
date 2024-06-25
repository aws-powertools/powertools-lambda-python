from typing import Any, Dict, List, Optional

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


class _FrozenListDict(List[Dict[str, List[str]]]):
    """
    Freezes a list of dictionaries containing lists of strings.

    This function takes a list of dictionaries where the values are lists of strings and converts it into
    a frozen set of frozen sets of frozen dictionaries. This is done by iterating over the input list,
    converting each dictionary's values (lists of strings) into frozen sets of strings, and then
    converting the resulting dictionary into a frozen dictionary. Finally, all these frozen dictionaries
    are collected into a frozen set of frozen sets.

    This operation is useful when you want to ensure the immutability of the data structure and make it
    hashable, which is required for certain operations like using it as a key in a dictionary or as an
    element in a set.

    Example: [{"TestAuth": ["test", "test1"]}]
    """

    def __hash__(self):
        hashable_items = []
        for item in self:
            hashable_items.extend((key, frozenset(value)) for key, value in item.items())
        return hash(frozenset(hashable_items))


def extract_origin_header(resolver_headers: Dict[str, Any]):
    """
    Extracts the 'origin' or 'Origin' header from the provided resolver headers.

    The 'origin' or 'Origin' header can be either a single header or a multi-header.

    Parameters
    ----------
    resolver_headers: Dict
        A dictionary containing the headers.

    Returns
    -------
    Optional[str]
        The value(s) of the origin header or None.
    """
    resolved_header = get_header_value(
        headers=resolver_headers,
        name="origin",
        default_value=None,
        case_sensitive=False,
    )
    if isinstance(resolved_header, list):
        return resolved_header[0]

    return resolved_header


def _validate_openapi_security_parameters(
    security: List[Dict[str, List[str]]],
    security_schemes: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    This function checks if all security requirements listed in the 'security'
    parameter are defined in the 'security_schemes' dictionary, as specified
    in the OpenAPI schema.

    Parameters
    ----------
    security: List[Dict[str, List[str]]]
        A list of security requirements
    security_schemes: Optional[Dict[str, Any]]
        A dictionary mapping security scheme names to their corresponding security scheme objects.

    Returns
    -------
    bool
        Whether list of security schemes match allowed security_schemes.
    """

    security_schemes = security_schemes or {}

    security_schema_match = all(key in security_schemes for sec in security for key in sec)

    return bool(security_schema_match and security_schemes)

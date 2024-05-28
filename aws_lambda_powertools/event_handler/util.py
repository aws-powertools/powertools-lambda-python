from typing import Any, Dict, FrozenSet, List

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
        return hash(FrozenSet({_FrozenDict({key: FrozenSet(self) for key, self in item.items()}) for item in self}))


def extract_origin_header(resolver_headers: Dict[str, Any]):
    """
    Extracts the 'origin' or 'Origin' header from the provided resolver headers.

    The 'origin' or 'Origin' header can be either a single header or a multi-header.

    Args:
        resolver_headers (Dict): A dictionary containing the headers.

    Returns:
        Optional[str]: The value(s) of the origin header or None.
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

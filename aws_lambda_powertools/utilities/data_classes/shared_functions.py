from __future__ import annotations

import base64
from typing import Any


def base64_decode(value: str) -> str:
    """
    Decodes a Base64-encoded string and returns the decoded value.

    Parameters
    ----------
    value: str
        The Base64-encoded string to decode.

    Returns
    -------
    str
        The decoded string value.
    """
    return base64.b64decode(value).decode("UTF-8")


def get_header_value(
    headers: dict[str, Any],
    name: str,
    default_value: str | None,
    case_sensitive: bool | None,
) -> str | None:
    """
    Get the value of a header by its name.

    Parameters
    ----------
    headers: Dict[str, str]
        The dictionary of headers.
    name: str
        The name of the header to retrieve.
    default_value: str, optional
        The default value to return if the header is not found. Default is None.
    case_sensitive: bool, optional
        Indicates whether the header name should be case-sensitive. Default is None.

    Returns
    -------
    str, optional
        The value of the header if found, otherwise the default value or None.
    """
    # If headers is NoneType, return default value
    if not headers:
        return default_value

    if case_sensitive:
        return headers.get(name, default_value)
    name_lower = name.lower()

    return next(
        # Iterate over the dict and do a case-insensitive key comparison
        (value for key, value in headers.items() if key.lower() == name_lower),
        # Default value is returned if no matches was found
        default_value,
    )


def get_query_string_value(
    query_string_parameters: dict[str, str] | None,
    name: str,
    default_value: str | None = None,
) -> str | None:
    """
    Retrieves the value of a query string parameter specified by the given name.

    Parameters
    ----------
    name: str
        The name of the query string parameter to retrieve.
    default_value: str, optional
        The default value to return if the parameter is not found. Defaults to None.

    Returns
    -------
    str. optional
        The value of the query string parameter if found, or the default value if not found.
    """
    params = query_string_parameters
    return default_value if params is None else params.get(name, default_value)

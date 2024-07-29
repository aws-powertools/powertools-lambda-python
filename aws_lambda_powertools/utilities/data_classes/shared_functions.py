import base64


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

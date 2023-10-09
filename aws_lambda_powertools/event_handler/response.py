from typing import Dict, List, Optional, Union

from aws_lambda_powertools.shared.cookies import Cookie


class Response:
    """Response data class that provides greater control over what is returned from the proxy event"""

    def __init__(
        self,
        status_code: int,
        content_type: Optional[str] = None,
        body: Union[str, bytes, None] = None,
        headers: Optional[Dict[str, Union[str, List[str]]]] = None,
        cookies: Optional[List[Cookie]] = None,
        compress: Optional[bool] = None,
    ):
        """

        Parameters
        ----------
        status_code: int
            Http status code, example 200
        content_type: str
            Optionally set the Content-Type header, example "application/json". Note this will be merged into any
            provided http headers
        body: Union[str, bytes, None]
            Optionally set the response body. Note: bytes body will be automatically base64 encoded
        headers: dict[str, Union[str, List[str]]]
            Optionally set specific http headers. Setting "Content-Type" here would override the `content_type` value.
        cookies: list[Cookie]
            Optionally set cookies.
        """
        self.status_code = status_code
        self.body = body
        self.base64_encoded = False
        self.headers: Dict[str, Union[str, List[str]]] = headers if headers else {}
        self.cookies = cookies or []
        self.compress = compress
        if content_type:
            self.headers.setdefault("Content-Type", content_type)

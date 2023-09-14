from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Optional

from aws_lambda_powertools.shared.types import List


class SameSite(Enum):
    """
    SameSite allows a server to define a cookie attribute making it impossible for
    the browser to send this cookie along with cross-site requests. The main
    goal is to mitigate the risk of cross-origin information leakage, and provide
    some protection against cross-site request forgery attacks.

    See https://tools.ietf.org/html/draft-ietf-httpbis-cookie-same-site-00 for details.
    """

    DEFAULT_MODE = ""
    LAX_MODE = "Lax"
    STRICT_MODE = "Strict"
    NONE_MODE = "None"


def _format_date(timestamp: datetime) -> str:
    # Specification example: Wed, 21 Oct 2015 07:28:00 GMT
    return timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT")


class Cookie:
    """
    A Cookie represents an HTTP cookie as sent in the Set-Cookie header of an
    HTTP response or the Cookie header of an HTTP request.

    See https://tools.ietf.org/html/rfc6265 for details.
    """

    def __init__(
        self,
        name: str,
        value: str,
        path: str = "",
        domain: str = "",
        secure: bool = True,
        http_only: bool = False,
        max_age: Optional[int] = None,
        expires: Optional[datetime] = None,
        same_site: Optional[SameSite] = None,
        custom_attributes: Optional[List[str]] = None,
    ):
        """

        Parameters
        ----------
        name: str
            The name of this cookie, for example session_id
        value: str
            The cookie value, for instance an uuid
        path: str
            The path for which this cookie is valid. Optional
        domain: str
            The domain for which this cookie is valid. Optional
        secure: bool
            Marks the cookie as secure, only sendable to the server with an encrypted request over the HTTPS protocol
        http_only: bool
            Enabling this attribute makes the cookie inaccessible to the JavaScript `Document.cookie` API
        max_age: Optional[int]
            Defines the period of time after which the cookie is invalid. Use negative values to force cookie deletion.
        expires: Optional[datetime]
            Defines a date where the permanent cookie expires.
        same_site: Optional[SameSite]
            Determines if the cookie should be sent to third party websites
        custom_attributes: Optional[List[str]]
            List of additional custom attributes to set on the cookie
        """
        self.name = name
        self.value = value
        self.path = path
        self.domain = domain
        self.secure = secure
        self.expires = expires
        self.max_age = max_age
        self.http_only = http_only
        self.same_site = same_site
        self.custom_attributes = custom_attributes

    def __str__(self) -> str:
        payload = StringIO()
        payload.write(f"{self.name}={self.value}")

        if self.path:
            payload.write(f"; Path={self.path}")

        if self.domain:
            payload.write(f"; Domain={self.domain}")

        if self.expires:
            payload.write(f"; Expires={_format_date(self.expires)}")

        if self.max_age:
            if self.max_age > 0:
                payload.write(f"; MaxAge={self.max_age}")
            else:
                # negative or zero max-age should be set to 0
                payload.write("; MaxAge=0")

        if self.http_only:
            payload.write("; HttpOnly")

        if self.secure:
            payload.write("; Secure")

        if self.same_site:
            payload.write(f"; SameSite={self.same_site.value}")

        if self.custom_attributes:
            for attr in self.custom_attributes:
                payload.write(f"; {attr}")

        return payload.getvalue()

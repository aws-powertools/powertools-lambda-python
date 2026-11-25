from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


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


def _to_utc(timestamp: date) -> datetime:
    # A date (which strftime accepted) means midnight
    if not isinstance(timestamp, datetime):
        timestamp = datetime(timestamp.year, timestamp.month, timestamp.day)

    # A naive datetime has no offset and is taken as UTC
    offset = timestamp.utcoffset() or timedelta(0)
    try:
        in_utc = timestamp.replace(tzinfo=None) - offset
    except OverflowError:
        # The instant is before year 1 or after year 9999: use the closest date format_datetime can write
        in_utc = datetime.min if offset > timedelta(0) else datetime.max
    return in_utc.replace(tzinfo=timezone.utc)


def _format_date(timestamp: date) -> str:
    # Imported on first use: the event handler imports this module but does not otherwise load email.utils
    from email.utils import format_datetime

    # Specification example: Wed, 21 Oct 2015 07:28:00 GMT
    # Unlike strftime, format_datetime uses English day and month names whatever the LC_TIME locale
    return format_datetime(_to_utc(timestamp), usegmt=True)


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
        max_age: int | None = None,
        expires: datetime | None = None,
        same_site: SameSite | None = None,
        custom_attributes: list[str] | None = None,
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
        max_age: int | None
            Defines the period of time after which the cookie is invalid. Use negative values to force cookie deletion.
        expires: datetime | None
            Defines a date where the permanent cookie expires. A timezone-aware datetime is sent as the same
            instant in GMT; a naive one is taken as UTC.
        same_site: SameSite | None
            Determines if the cookie should be sent to third party websites
        custom_attributes: list[str] | None
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

        if self.max_age is not None:
            if self.max_age > 0:
                payload.write(f"; Max-Age={self.max_age}")
            else:
                # negative or zero max-age should be set to 0
                payload.write("; Max-Age=0")

        if self.http_only:
            payload.write("; HttpOnly")

        if self.secure:
            payload.write("; Secure")

        # DEFAULT_MODE leaves the attribute out, so the browser applies its own default
        if self.same_site and self.same_site.value:
            payload.write(f"; SameSite={self.same_site.value}")

        if self.custom_attributes:
            for attr in self.custom_attributes:
                payload.write(f"; {attr}")

        return payload.getvalue()

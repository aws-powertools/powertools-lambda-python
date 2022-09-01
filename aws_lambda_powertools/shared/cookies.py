from datetime import datetime
from enum import Enum
from io import StringIO
from typing import List, Optional


class SameSite(Enum):
    DEFAULT_MODE = ""
    LAX_MODE = "Lax"
    STRICT_MODE = "Strict"
    NONE_MODE = "None"


def _getdate(timestamp: datetime) -> str:
    return timestamp.strftime("%a, %d %b %Y %H:%M:%S GMT")


class Cookie:
    def __init__(
        self,
        name: str,
        value: str,
        path: Optional[str] = None,
        domain: Optional[str] = None,
        expires: Optional[datetime] = None,
        max_age: Optional[int] = None,
        secure: Optional[bool] = None,
        http_only: Optional[bool] = None,
        same_site: Optional[SameSite] = None,
        custom_attributes: Optional[List[str]] = None,
    ):
        self.name = name
        self.value = value
        self.path = path
        self.domain = domain
        self.expires = expires
        self.max_age = max_age
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site
        self.custom_attributes = custom_attributes

    def __str__(self) -> str:
        payload = StringIO()
        payload.write(f"{self.name}={self.value}")

        if self.path and len(self.path) > 0:
            payload.write(f"; Path={self.path}")

        if self.domain and len(self.domain) > 0:
            payload.write(f"; Domain={self.domain}")

        if self.expires:
            payload.write(f"; Expires={_getdate(self.expires)}")

        if self.max_age:
            if self.max_age > 0:
                payload.write(f"; MaxAge={self.max_age}")
            if self.max_age < 0:
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

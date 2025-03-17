from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aws_lambda_powertools.event_handler.openapi.constants import (
    DEFAULT_API_VERSION,
    DEFAULT_OPENAPI_TITLE,
    DEFAULT_OPENAPI_VERSION,
)

if TYPE_CHECKING:
    from aws_lambda_powertools.event_handler.openapi.models import (
        Contact,
        License,
        SecurityScheme,
        Server,
        Tag,
    )


@dataclass
class OpenAPIConfig:
    """Configuration class for OpenAPI specification.

    This class holds all the necessary configuration parameters to generate an OpenAPI specification.

    Parameters
    ----------
    title: str
        The title of the application.
    version: str
        The version of the OpenAPI document (which is distinct from the OpenAPI Specification version or the API
    openapi_version: str, default = "3.0.0"
        The version of the OpenAPI Specification (which the document uses).
    summary: str, optional
        A short summary of what the application does.
    description: str, optional
        A verbose explanation of the application behavior.
    tags: list[Tag, str], optional
        A list of tags used by the specification with additional metadata.
    servers: list[Server], optional
        An array of Server Objects, which provide connectivity information to a target server.
    terms_of_service: str, optional
        A URL to the Terms of Service for the API. MUST be in the format of a URL.
    contact: Contact, optional
        The contact information for the exposed API.
    license_info: License, optional
        The license information for the exposed API.
    security_schemes: dict[str, SecurityScheme]], optional
        A declaration of the security schemes available to be used in the specification.
    security: list[dict[str, list[str]]], optional
        A declaration of which security mechanisms are applied globally across the API.
    openapi_extensions: Dict[str, Any], optional
        Additional OpenAPI extensions as a dictionary.

    Example
    --------
    >>> config = OpenAPIConfig(
    ...     title="My API",
    ...     version="1.0.0",
    ...     description="This is my API description",
    ...     contact=Contact(name="API Support", email="support@example.com"),
    ...     servers=[Server(url="https://api.example.com/v1")]
    ... )
    """

    title: str = DEFAULT_OPENAPI_TITLE
    version: str = DEFAULT_API_VERSION
    openapi_version: str = DEFAULT_OPENAPI_VERSION
    summary: str | None = None
    description: str | None = None
    tags: list[Tag | str] | None = None
    servers: list[Server] | None = None
    terms_of_service: str | None = None
    contact: Contact | None = None
    license_info: License | None = None
    security_schemes: dict[str, SecurityScheme] | None = None
    security: list[dict[str, list[str]]] | None = None
    openapi_extensions: dict[str, Any] | None = None

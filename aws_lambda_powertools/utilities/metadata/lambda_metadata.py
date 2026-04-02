"""
Lambda Metadata Service client

Fetches execution environment metadata from the Lambda Metadata Endpoint,
with caching for the sandbox lifetime.
"""

from __future__ import annotations

import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from json import JSONDecodeError
from json import loads as json_loads
from typing import Any

from aws_lambda_powertools.shared.constants import (
    LAMBDA_INITIALIZATION_TYPE,
    LAMBDA_METADATA_API_ENV,
    LAMBDA_METADATA_TOKEN_ENV,
    METADATA_API_VERSION,
    METADATA_DEFAULT_TIMEOUT_SECS,
    METADATA_PATH,
    POWERTOOLS_DEV_ENV,
)
from aws_lambda_powertools.utilities.metadata.exceptions import LambdaMetadataError

logger = logging.getLogger(__name__)

_cache: dict[str, Any] = {}


@dataclass(frozen=True)
class LambdaMetadata:
    """Lambda execution environment metadata returned by the metadata endpoint."""

    availability_zone_id: str | None = None
    """The Availability Zone ID where the function is executing (e.g. ``use1-az1``)."""

    _raw: dict[str, Any] = field(default_factory=dict, repr=False)
    """Full raw response for forward-compatibility with future fields."""


def _is_lambda_environment() -> bool:
    """Check whether we are running inside a Lambda execution environment."""
    return os.environ.get(LAMBDA_INITIALIZATION_TYPE, "") != ""


def _is_dev_mode() -> bool:
    """Check whether POWERTOOLS_DEV is enabled."""
    return os.environ.get(POWERTOOLS_DEV_ENV, "false").strip().lower() in ("true", "1")


def _build_metadata(data: dict[str, Any]) -> LambdaMetadata:
    """Build a LambdaMetadata dataclass from the raw endpoint response."""
    return LambdaMetadata(
        availability_zone_id=data.get("AvailabilityZoneID"),
        _raw=data,
    )


def _fetch_metadata(timeout: float = METADATA_DEFAULT_TIMEOUT_SECS) -> dict[str, Any]:
    """
    Fetch metadata from the Lambda Metadata Endpoint via HTTP.

    Parameters
    ----------
    timeout : float
        Request timeout in seconds.

    Returns
    -------
    dict[str, Any]
        Parsed JSON response from the metadata endpoint.

    Raises
    ------
    LambdaMetadataError
        If required environment variables are missing, the endpoint returns
        a non-200 status, or the response cannot be parsed.
    """
    api = os.environ.get(LAMBDA_METADATA_API_ENV)
    token = os.environ.get(LAMBDA_METADATA_TOKEN_ENV)

    if not api:
        raise LambdaMetadataError(
            f"Environment variable {LAMBDA_METADATA_API_ENV} is not set. Ensure {LAMBDA_METADATA_API_ENV} is set.",
        )
    if not token:
        raise LambdaMetadataError(
            f"Environment variable {LAMBDA_METADATA_TOKEN_ENV} is not set. Ensure {LAMBDA_METADATA_TOKEN_ENV} is set.",
        )

    url = f"http://{api}/{METADATA_API_VERSION}{METADATA_PATH}"
    logger.debug("Fetching Lambda metadata from: %s", url)

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
            status = resp.status
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise LambdaMetadataError(
            f"Metadata request failed with status {exc.code}",
            status_code=exc.code,
        ) from exc
    except Exception as exc:
        raise LambdaMetadataError(f"Failed to fetch Lambda metadata: {exc}") from exc

    if status != 200:
        raise LambdaMetadataError(
            f"Metadata request failed with status {status}",
            status_code=status,
        )

    try:
        data: dict[str, Any] = json_loads(body)
    except (JSONDecodeError, TypeError) as exc:
        raise LambdaMetadataError(f"Failed to parse metadata response: {exc}") from exc

    logger.debug("Lambda metadata response: %s", data)
    return data


def get_lambda_metadata(*, timeout: float = METADATA_DEFAULT_TIMEOUT_SECS) -> LambdaMetadata:
    """
    Retrieve Lambda execution environment metadata.

    Returns cached metadata on subsequent calls. When not running in a Lambda
    environment (local dev, tests) or when ``POWERTOOLS_DEV`` is enabled,
    returns an empty ``LambdaMetadata``.

    Parameters
    ----------
    timeout : float
        HTTP request timeout in seconds (default 1.0).

    Returns
    -------
    LambdaMetadata
        Metadata about the current execution environment.

    Raises
    ------
    LambdaMetadataError
        If the metadata endpoint is unavailable or returns an error.

    Example
    -------
        >>> from aws_lambda_powertools.utilities.metadata import get_lambda_metadata
        >>> metadata = get_lambda_metadata()
        >>> metadata.availability_zone_id  # e.g. "use1-az1"
    """
    if _is_dev_mode() or not _is_lambda_environment():
        return LambdaMetadata()

    if _cache:
        return _build_metadata(_cache)

    data = _fetch_metadata(timeout=timeout)
    _cache.update(data)
    return _build_metadata(_cache)


def clear_metadata_cache() -> None:
    """
    Clear the cached metadata.

    Useful for testing or when you need to force a fresh fetch
    (e.g. after SnapStart restore).
    """
    _cache.clear()

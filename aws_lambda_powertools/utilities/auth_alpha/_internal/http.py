from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

import urllib3
from urllib3.poolmanager import pool_classes_by_scheme

from aws_lambda_powertools.utilities.auth_alpha._internal.deadline import Deadline, RequestError
from aws_lambda_powertools.utilities.auth_alpha._internal.transport import (
    DeadlineHTTPSConnectionPool,
    response_deadline,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from urllib3.connectionpool import HTTPConnectionPool

_MAX_JSON_BYTES = 1024 * 1024


class HTTPClient:
    """HTTPS transport with bounded JSON responses and no implicit redirects/retries."""

    def __init__(self) -> None:
        self.pool = urllib3.PoolManager(cert_reqs="CERT_REQUIRED")
        self.pool.pool_classes_by_scheme = pool_classes_by_scheme.copy()
        pool_classes = cast("dict[str, type[HTTPConnectionPool]]", self.pool.pool_classes_by_scheme)
        pool_classes["https"] = DeadlineHTTPSConnectionPool

    def _open_response(
        self,
        method: str,
        url: str,
        deadline: Deadline,
        **options: Any,
    ) -> urllib3.response.BaseHTTPResponse:
        with response_deadline(deadline):
            return self.pool.request(
                method,
                url,
                timeout=urllib3.Timeout(total=deadline.remaining()),
                retries=False,
                redirect=False,
                preload_content=False,
                **options,
            )

    def json_request(
        self,
        method: str,
        url: str,
        deadline: Deadline,
        *,
        body: bytes | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        response = None
        try:
            response = self._open_response(
                method,
                url,
                deadline,
                body=body,
                headers=headers,
            )
            if response.status != 200:
                deadline.remaining()
                return response.status, {}
            data = self._read_json(response, deadline)
            return response.status, data
        except (urllib3.exceptions.HTTPError, OSError):
            raise RequestError(retryable=True) from None
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    @staticmethod
    def _read_json(response: urllib3.response.BaseHTTPResponse, deadline: Deadline) -> dict[str, Any]:
        content = HTTPClient._read_body(response, deadline, limit=_MAX_JSON_BYTES, decode_content=False)
        try:
            data = json.loads(content)
        except (ValueError, UnicodeError, RecursionError):
            raise RequestError() from None
        if not isinstance(data, dict):
            raise RequestError()
        return data

    def request(
        self,
        method: str,
        url: str,
        deadline: Deadline,
        *,
        headers: Mapping[str, str],
        **options: Any,
    ) -> urllib3.response.HTTPResponse:
        """Buffer an authenticated response within one network time budget."""
        response = None
        try:
            response = self._open_response(
                method,
                url,
                deadline,
                headers=headers,
                **options,
            )
            content = self._read_body(response, deadline)
            return urllib3.HTTPResponse(
                body=content,
                status=response.status,
                headers=response.headers,
                reason=response.reason,
                version=response.version,
                request_method=method,
                request_url=url,
                decode_content=False,
            )
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    @staticmethod
    def _read_body(
        response: urllib3.response.BaseHTTPResponse,
        deadline: Deadline,
        *,
        limit: int | None = None,
        decode_content: bool = True,
    ) -> bytes:
        chunks = bytearray()
        while True:
            deadline.remaining()
            size = 65536 if limit is None else min(65536, limit + 1 - len(chunks))
            chunk = response.read1(size, decode_content=decode_content)
            deadline.remaining()
            if not chunk:
                break
            chunks.extend(chunk)
            if limit is not None and len(chunks) > limit:
                raise RequestError()
        return bytes(chunks)

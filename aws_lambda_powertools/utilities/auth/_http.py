from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import urllib3
from urllib3.connection import HTTPConnection

from aws_lambda_powertools.utilities.auth._deadline import Deadline, RequestError

if TYPE_CHECKING:
    from collections.abc import Mapping

_MAX_JSON_BYTES = 1024 * 1024


class HTTPClient:
    """HTTPS transport with bounded JSON responses and no implicit redirects/retries."""

    def __init__(self) -> None:
        self.pool = urllib3.PoolManager(cert_reqs="CERT_REQUIRED")

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
            response = self.pool.request(
                method,
                url,
                body=body,
                headers=headers,
                timeout=urllib3.Timeout(total=deadline.remaining()),
                retries=False,
                redirect=False,
                preload_content=False,
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
        chunks = bytearray()
        while True:
            remaining = deadline.remaining()
            connection = response.connection
            if isinstance(connection, HTTPConnection) and connection.sock is not None:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(65536, _MAX_JSON_BYTES + 1 - len(chunks)), decode_content=False)
            deadline.remaining()
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > _MAX_JSON_BYTES:
                raise RequestError()
        try:
            data = json.loads(chunks)
        except (ValueError, UnicodeError, RecursionError):
            raise RequestError() from None
        if not isinstance(data, dict):
            raise RequestError()
        return data

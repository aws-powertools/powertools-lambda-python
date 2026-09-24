from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from http.client import HTTPResponse
from io import BufferedReader, RawIOBase
from typing import TYPE_CHECKING

from urllib3.connection import HTTPSConnection
from urllib3.connectionpool import HTTPSConnectionPool

if TYPE_CHECKING:
    from collections.abc import Iterator
    from socket import socket
    from typing import Protocol

    from typing_extensions import Buffer

    from aws_lambda_powertools.utilities.auth_alpha._internal.deadline import Deadline

    class _ResponseStream(Protocol):
        def readinto1(self, buffer: Buffer, /) -> int: ...
        def close(self) -> None: ...


_current_deadline: ContextVar[Deadline] = ContextVar("auth_response_deadline")


@contextmanager
def response_deadline(deadline: Deadline) -> Iterator[None]:
    """Pass the operation's deadline to responses created by this synchronous call."""
    token = _current_deadline.set(deadline)
    try:
        yield
    finally:
        _current_deadline.reset(token)


class _DeadlineReader(RawIOBase):
    """Check the original budget on every refill, including HTTP framing reads."""

    def __init__(self, stream: _ResponseStream, sock: socket, deadline: Deadline) -> None:
        super().__init__()
        self._stream = stream
        self._socket = sock
        self._deadline = deadline

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Buffer, /) -> int:
        self._socket.settimeout(self._deadline.remaining())
        # Unlike readinto(), readinto1() performs at most one underlying read.
        count = self._stream.readinto1(buffer)
        self._deadline.remaining()
        return count

    def close(self) -> None:
        try:
            self._stream.close()
        finally:
            super().close()


class _DeadlineResponse(HTTPResponse):
    def __init__(
        self,
        sock: socket,
        debuglevel: int = 0,
        method: str | None = None,
        url: str | None = None,
    ) -> None:
        deadline = _current_deadline.get()
        super().__init__(sock, debuglevel=debuglevel, method=method, url=url)
        # Retain the wrapper through body consumption: read1() can also parse
        # chunk-size lines, delimiters and trailers before returning to our loop.
        # The stream owns the socket reference even for Connection: close.
        self.fp = BufferedReader(_DeadlineReader(self.fp, sock, deadline), buffer_size=8192)


class _DeadlineHTTPSConnection(HTTPSConnection):
    response_class = _DeadlineResponse


class DeadlineHTTPSConnectionPool(HTTPSConnectionPool):
    """Use the stdlib response hook without overriding urllib3's request machinery."""

    ConnectionCls = _DeadlineHTTPSConnection

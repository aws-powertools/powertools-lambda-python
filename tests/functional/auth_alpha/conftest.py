import io
import json
import time
from collections import deque

import pytest
import urllib3


class FakeHTTP:
    """In-memory authentication endpoints at the HTTP transport boundary."""

    def __init__(self):
        self.responses = {}
        self.requests = []

    def serve(self, url, body, *, status=200, method="GET"):
        self.responses[(method, url)] = deque([(status, body)])

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        responses = self.responses[(method, url)]
        status, body = responses[0] if len(responses) == 1 else responses.popleft()
        if callable(body):
            body = body()
        if isinstance(body, Exception):
            raise body
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        return urllib3.HTTPResponse(
            body=io.BytesIO(payload),
            headers={"content-type": "application/json"},
            status=status,
            preload_content=False,
        )


@pytest.fixture
def http(monkeypatch):
    transport = FakeHTTP()
    monkeypatch.setattr(urllib3, "PoolManager", lambda **kwargs: transport)
    return transport


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = 1000.0

        def __call__(self):
            return self.now

        def advance(self, seconds):
            self.now += seconds

    clock = Clock()
    monkeypatch.setattr(time, "monotonic", clock)
    return clock

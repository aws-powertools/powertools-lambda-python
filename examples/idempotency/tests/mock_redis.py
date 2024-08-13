from __future__ import annotations

import time as t
from typing import dict


# Mock redis class that includes all operations we used in Idempotency
class MockRedis:
    def __init__(self, decode_responses, cache: dict, **kwargs):
        self.cache = cache or {}
        self.expire_dict: dict = {}
        self.decode_responses = decode_responses
        self.acl: dict = {}
        self.username = ""

    def hset(self, name, mapping):
        self.expire_dict.pop(name, {})
        self.cache[name] = mapping

    def from_url(self, url: str):
        pass

    def expire(self, name, time):
        self.expire_dict[name] = t.time() + time

    # return {} if no match
    def hgetall(self, name):
        if self.expire_dict.get(name, t.time() + 1) < t.time():
            self.cache.pop(name, {})
        return self.cache.get(name, {})

    def get_connection_kwargs(self):
        return {"decode_responses": self.decode_responses}

    def auth(self, username, **kwargs):
        self.username = username

    def delete(self, name):
        self.cache.pop(name, {})

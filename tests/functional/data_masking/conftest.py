from __future__ import annotations

from typing import Tuple

from pytest_socket import disable_socket


def pytest_runtest_setup():
    """Disable Unix and TCP sockets for Data masking tests"""
    disable_socket()


class FakeEncryptionClient:
    ENCRYPTION_HEADER = "test"

    def encrypt(self, source: bytes | str, **kwargs) -> Tuple[bytes, str]:
        if isinstance(source, str):
            return source.encode(), self.ENCRYPTION_HEADER

        return source, self.ENCRYPTION_HEADER

    def decrypt(self, source: bytes, **kwargs) -> Tuple[bytes, str]:
        return source, "dummy_decryption_header"

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing.lambda_client_context_mobile_client import (
        LambdaClientContextMobileClient,
    )


class LambdaClientContext:
    _client: LambdaClientContextMobileClient
    _custom: dict[str, Any]
    _env: dict[str, Any]

    @property
    def client(self) -> LambdaClientContextMobileClient:
        """Client context that's provided to Lambda by the client application."""
        return self._client

    @property
    def custom(self) -> dict[str, Any]:
        """A dict of custom values set by the mobile client application."""
        return self._custom

    @property
    def env(self) -> dict[str, Any]:
        """A dict of environment information provided by the AWS SDK."""
        return self._env

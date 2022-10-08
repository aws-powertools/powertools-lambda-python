# -*- coding: utf-8 -*-
from typing import Any, Dict

from aws_lambda_powertools.utilities.typing.lambda_client_context_mobile_client import (
    LambdaClientContextMobileClient,
)


class LambdaClientContext(object):
    _client: LambdaClientContextMobileClient
    _custom: Dict[str, Any]
    _env: Dict[str, Any]

    @property
    def client(self) -> LambdaClientContextMobileClient:
        """Client context that's provided to Lambda by the client application."""
        return self._client

    @property
    def custom(self) -> Dict[str, Any]:
        """A dict of custom values set by the mobile client application."""
        return self._custom

    @property
    def env(self) -> Dict[str, Any]:
        """A dict of environment information provided by the AWS SDK."""
        return self._env

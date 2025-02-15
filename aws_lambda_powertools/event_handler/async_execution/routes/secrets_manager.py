from __future__ import annotations

from typing import Any, Callable

from aws_lambda_powertools.utilities.data_classes.secrets_manager_event import (
    SecretsManagerEvent,
)

from .base import BaseRoute


class SecretsManagerRoute(BaseRoute):
    secret_id: str | None
    secret_name_prefix: str | None

    def __init__(self, func: Callable, secret_id: str | None = None, secret_name_prefix: str | None = None):
        self.func = func
        self.secret_id = secret_id
        self.secret_name_prefix = secret_name_prefix

        if not self.secret_id and not self.secret_name_prefix:
            raise ValueError("secret_id, or secret_name_prefix must be not null")

    def match(self, event: dict[str, Any]) -> tuple[Callable, SecretsManagerEvent] | None:
        if not isinstance(event, dict):
            return None

        secret_id: str | None = event.get("SecretId")

        if not secret_id:
            return None
        elif self.secret_id and self.secret_name_prefix:
            part = secret_id.split(":")
            secret_name = part[-1]
            if self.secret_id == secret_id and secret_name.find(self.secret_name_prefix) == 0:
                return self.func, SecretsManagerEvent(event)
        elif self.secret_id:
            if self.secret_id == secret_id:
                return self.func, SecretsManagerEvent(event)
        elif self.secret_name_prefix:
            part = secret_id.split(":")
            secret_name = part[-1]
            if secret_name.find(self.secret_name_prefix) == 0:
                return self.func, SecretsManagerEvent(event)

        return None

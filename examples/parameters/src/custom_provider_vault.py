import json
from typing import Dict

from hvac import Client

from aws_lambda_powertools.utilities.parameters import BaseProvider


class VaultProvider(BaseProvider):
    def __init__(self, vault_url: str, vault_token: str) -> None:

        super().__init__()

        self.vault_client = Client(url=vault_url, verify=False, timeout=10)
        self.vault_client.token = vault_token

    def _get(self, name: str, **sdk_options) -> str:

        # for example proposal, the mountpoint is always /secret
        kv_configuration = self.vault_client.secrets.kv.v2.read_secret(path=name)

        return json.dumps(kv_configuration["data"]["data"])

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:

        list_secrets = {}
        all_secrets = self.vault_client.secrets.kv.v2.list_secrets(path=path)

        # for example proposal, the mountpoint is always /secret
        for secret in all_secrets["data"]["keys"]:
            kv_configuration = self.vault_client.secrets.kv.v2.read_secret(path=secret)

            for key, value in kv_configuration["data"]["data"].items():
                list_secrets[key] = value

        return list_secrets

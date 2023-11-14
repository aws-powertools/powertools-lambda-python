import json
from aws_lambda_powertools.utilities._data_masking.provider import BaseProvider


class MyCustomEncryption(BaseProvider):
    def __init__(self, secret):
        super().__init__()
        self.secret = secret

    def encrypt(self, data: str) -> str:
        if data is None:
            return data
        return json.dumps(data)

    def decrypt(self, data: str) -> str:
        if data is None:
            return data
        return json.loads(data)

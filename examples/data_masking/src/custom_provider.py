from itsdangerous.url_safe import URLSafeSerializer

from aws_lambda_powertools.utilities.data_masking.provider import BaseProvider


class MyCustomEncryption(BaseProvider):
    def __init__(self, secret):
        super().__init__()
        self.secret = URLSafeSerializer(secret)

    def encrypt(self, data: str) -> str:
        if data is None:
            return data
        return self.secret.dumps(data)

    def decrypt(self, data: str) -> str:
        if data is None:
            return data
        return self.secret.loads(data)

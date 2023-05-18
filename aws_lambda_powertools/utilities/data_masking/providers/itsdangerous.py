from itsdangerous.url_safe import URLSafeSerializer

from aws_lambda_powertools.utilities.data_masking.provider import Provider


class ItsDangerousProvider(Provider):
    def __init__(self, keys, salt=None):
        self.keys = keys
        self.salt = salt

    def encrypt(self, data, **kwargs):
        if data is None:
            return data

        serialized = URLSafeSerializer(self.keys, salt=self.salt, **kwargs)
        return serialized.dumps(data)

    def decrypt(self, data, **kwargs):
        if data is None:
            return data

        serialized = URLSafeSerializer(self.keys, salt=self.salt, **kwargs)
        return serialized.loads(data)

from itsdangerous.url_safe import URLSafeSerializer

from aws_lambda_powertools.utilities.data_masking.provider import Provider


class ItsDangerousProvider(Provider):
    def __init__(
        self,
        keys,
        salt=None,
        serializer=None,
        serializer_kwargs=None,
        signer=None,
        signer_kwargs=None,
        fallback_signers=None,
    ):
        self.keys = keys
        self.salt = salt
        self.serializer = serializer
        self.serializer_kwargs = serializer_kwargs
        self.signer = signer
        self.signer_kwargs = signer_kwargs
        self.fallback_signers = fallback_signers

    def encrypt(self, data):
        if data is None:
            return data

        serialized = URLSafeSerializer(
            self.keys,
            salt=self.salt,
            serializer=None,
            serializer_kwargs=None,
            signer=None,
            signer_kwargs=None,
            fallback_signers=None,
        )
        return serialized.dumps(data)

    def decrypt(self, data):
        if data is None:
            return data

        serialized = URLSafeSerializer(
            self.keys,
            salt=self.salt,
            serializer=None,
            serializer_kwargs=None,
            signer=None,
            signer_kwargs=None,
            fallback_signers=None,
        )
        return serialized.loads(data)

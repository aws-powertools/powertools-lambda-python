"""
Idempotency errors
"""


from typing import Optional, Union


class BaseError(Exception):
    """
    Base error class that overwrites the way exception and extra information is printed.
    See https://github.com/aws-powertools/powertools-lambda-python/issues/1772
    """

    def __init__(self, *args: Optional[Union[str, Exception]]):
        self.message = str(args[0]) if args else ""
        self.details = "".join(str(arg) for arg in args[1:]) if args[1:] else None

    def __str__(self):
        """
        Return all arguments formatted or original message
        """
        if self.message and self.details:
            return f"{self.message} - ({self.details})"
        return self.message


class DataMaskingUnsupportedTypeError(BaseError):
    """
    UnsupportedType Error
    """


class DataMaskingDecryptKeyError(BaseError):
    """
    Decrypting with an invalid AWS KMS Key ARN.
    """


class DataMaskingEncryptKeyError(BaseError):
    """
    Encrypting with an invalid AWS KMS Key ARN.
    """

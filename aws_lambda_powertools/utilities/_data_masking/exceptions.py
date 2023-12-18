class DataMaskingUnsupportedTypeError(Exception):
    """
    UnsupportedType Error
    """


class DataMaskingDecryptKeyError(Exception):
    """
    Decrypting with an invalid AWS KMS Key ARN.
    """


class DataMaskingEncryptKeyError(Exception):
    """
    Encrypting with an invalid AWS KMS Key ARN.
    """


class DataMaskingDecryptValueError(Exception):
    """
    Decrypting an invalid field.
    """


class DataMaskingContextMismatchError(Exception):
    """
    Decrypting with the incorrect encryption context.
    """


class DataMaskingFieldNotFoundError(Exception):
    """
    Field not found.
    """

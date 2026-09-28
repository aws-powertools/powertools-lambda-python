class DataMaskingError(Exception):
    """
    Base exception for data masking failures.
    """


class DataMaskingUnsupportedTypeError(DataMaskingError):
    """
    UnsupportedType Error
    """


class DataMaskingDecryptKeyError(DataMaskingError):
    """
    Decrypting with an invalid AWS KMS Key ARN.
    """


class DataMaskingEncryptKeyError(DataMaskingError):
    """
    Encrypting with an invalid AWS KMS Key ARN.
    """


class DataMaskingDecryptValueError(DataMaskingError):
    """
    Decrypting an invalid field.
    """


class DataMaskingContextMismatchError(DataMaskingError):
    """
    Decrypting with the incorrect encryption context.
    """


class DataMaskingFieldNotFoundError(DataMaskingError):
    """
    Field not found.
    """

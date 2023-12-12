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

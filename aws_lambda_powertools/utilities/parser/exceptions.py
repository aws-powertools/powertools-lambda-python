class InvalidEnvelopeError(Exception):
    """Input envelope is not callable and instance of BaseEnvelope"""


class InvalidModelTypeError(Exception):
    """Input data model does not implement BaseModel"""

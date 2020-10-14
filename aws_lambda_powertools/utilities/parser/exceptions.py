class InvalidEnvelopeError(Exception):
    """Input envelope is not callable and instance of BaseEnvelope"""


class ModelValidationError(Exception):
    """Input data does not conform with model"""


class InvalidModelTypeError(Exception):
    """Input data model does not implement BaseModel"""

class InvalidEnvelopeError(Exception):
    """Input envelope is not callable and instance of BaseEnvelope"""


class SchemaValidationError(Exception):
    """Input data does not conform with schema"""

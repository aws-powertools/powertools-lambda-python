from ...exceptions import InvalidEnvelopeExpressionError


class SchemaValidationError(Exception):
    """When serialization fail schema validation"""


class InvalidSchemaFormatError(Exception):
    """When JSON Schema is in invalid format"""


__all__ = ["SchemaValidationError", "InvalidSchemaFormatError", "InvalidEnvelopeExpressionError"]

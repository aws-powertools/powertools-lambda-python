class SchemaValidationError(Exception):
    """When serialization fail schema validation"""


class InvalidSchemaFormatError(Exception):
    """When JSON Schema is in invalid format"""


class InvalidEnvelopeExpressionError(Exception):
    """When JMESPath fails to parse expression"""

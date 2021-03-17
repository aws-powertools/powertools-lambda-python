class SchemaValidationError(Exception):
    """When serialization fail schema validation"""

    pass


class InvalidSchemaFormatError(Exception):
    """When JSON Schema is in invalid format"""

    pass


class InvalidEnvelopeExpressionError(Exception):
    """When JMESPath fails to parse expression"""

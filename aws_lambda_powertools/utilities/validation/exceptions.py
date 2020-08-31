class SchemaValidationError(Exception):
    """When serialization fail schema validation"""

    pass


class InvalidSchemaError(Exception):
    """When JSON Schema is in invalid format"""

    pass


class InvalidEnvelopeExpressionError(Exception):
    """When JMESPath fails to parse expression"""

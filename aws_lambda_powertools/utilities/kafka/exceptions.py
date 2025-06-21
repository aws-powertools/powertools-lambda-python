class KafkaConsumerAvroSchemaParserError(Exception):
    """
    Error raised when parsing Avro schema definition fails.
    """


class KafkaConsumerDeserializationFormatMismatch(Exception):
    """
    Error raised when deserialization format is incompatible
    """


class KafkaConsumerDeserializationError(Exception):
    """
    Error raised when message deserialization fails.
    """


class KafkaConsumerMissingSchemaError(Exception):
    """
    Error raised when a required schema is not provided.
    """


class KafkaConsumerOutputSerializerError(Exception):
    """
    Error raised when output serializer fails.
    """

class KafkaConsumerAvroSchemaParserError(Exception):
    """
    Error raised when parsing Avro schema definition fails.
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

class KafkaConsumerAvroSchemaMismatchError(Exception):
    """
    Avro schema mismatch
    """


class KafkaConsumerDeserializationError(Exception):
    """
    Avro schema impossible to deserialize
    """


class KafkaConsumerAvroMissingSchemaError(Exception):
    """
    Avro schema mismatch
    """

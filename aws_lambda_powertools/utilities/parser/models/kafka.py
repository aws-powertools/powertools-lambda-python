from datetime import datetime
from typing import Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, field_validator

from aws_lambda_powertools.shared.functions import base64_decode, bytes_to_string

SERVERS_DELIMITER = ","


class KafkaRecordModel(BaseModel):
    topic: str
    partition: int
    offset: int
    timestamp: datetime
    timestampType: str
    key: Optional[bytes] = None
    value: Union[str, Type[BaseModel]]
    headers: List[Dict[str, bytes]]

    # key is optional; only decode if not None
    @field_validator("key", mode="before")
    def decode_key(cls, value):
        if value is not None:
            return base64_decode(value)
        return value

    @field_validator("value", mode="before")
    def data_base64_decode(cls, value):
        as_bytes = base64_decode(value)
        return bytes_to_string(as_bytes)

    @field_validator("headers", mode="before")
    def decode_headers_list(cls, value):
        for header in value:
            for key, values in header.items():
                header[key] = bytes(values)
        return value


class KafkaBaseEventModel(BaseModel):
    bootstrapServers: List[str]
    records: Dict[str, List[KafkaRecordModel]]

    @field_validator("bootstrapServers", mode="before")
    def split_servers(cls, value):
        return None if not value else value.split(SERVERS_DELIMITER)


class KafkaSelfManagedEventModel(KafkaBaseEventModel):
    """Self-managed Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    """

    eventSource: Literal["SelfManagedKafka"]


class KafkaMskEventModel(KafkaBaseEventModel):
    """Fully-managed AWS Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    eventSource: Literal["aws:kafka"]
    eventSourceArn: str

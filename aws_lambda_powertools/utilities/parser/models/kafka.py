from datetime import datetime
from typing import Dict, List, Type, Union

from pydantic import BaseModel, validator

from aws_lambda_powertools.shared.functions import base64_decode, bytes_to_string
from aws_lambda_powertools.utilities.parser.types import Literal

SERVERS_DELIMITER = ","


class KafkaRecordModel(BaseModel):
    topic: str
    partition: int
    offset: int
    timestamp: datetime
    timestampType: str
    key: bytes
    value: Union[str, Type[BaseModel]]
    headers: List[Dict[str, bytes]]

    # validators
    _decode_key = validator("key", allow_reuse=True)(base64_decode)

    @validator("value", pre=True, allow_reuse=True)
    def data_base64_decode(cls, value):
        as_bytes = base64_decode(value)
        return bytes_to_string(as_bytes)

    @validator("headers", pre=True, allow_reuse=True)
    def decode_headers_list(cls, value):
        for header in value:
            for key, values in header.items():
                header[key] = bytes(values)
        return value


class KafkaBaseEventModel(BaseModel):
    bootstrapServers: List[str]
    records: Dict[str, List[KafkaRecordModel]]

    @validator("bootstrapServers", pre=True, allow_reuse=True)
    def split_servers(cls, value):
        return None if not value else value.split(SERVERS_DELIMITER)


class KafkaSelfManagedEventModel(KafkaBaseEventModel):
    """Self-managed Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    """

    eventSource: Literal["aws:SelfManagedKafka"]


class KafkaMskEventModel(KafkaBaseEventModel):
    """Fully-managed AWS Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    eventSource: Literal["aws:kafka"]
    eventSourceArn: str

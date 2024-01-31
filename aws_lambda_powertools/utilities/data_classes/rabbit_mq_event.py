from typing import Any, Dict, List

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.shared_functions import base64_decode


class BasicProperties(DictWrapper):
    @property
    def content_type(self) -> str:
        return self["contentType"]

    @property
    def content_encoding(self) -> str:
        return self["contentEncoding"]

    @property
    def headers(self) -> Dict[str, Any]:
        return self["headers"]

    @property
    def delivery_mode(self) -> int:
        return self["deliveryMode"]

    @property
    def priority(self) -> int:
        return self["priority"]

    @property
    def correlation_id(self) -> str:
        return self["correlationId"]

    @property
    def reply_to(self) -> str:
        return self["replyTo"]

    @property
    def expiration(self) -> str:
        return self["expiration"]

    @property
    def message_id(self) -> str:
        return self["messageId"]

    @property
    def timestamp(self) -> str:
        return self["timestamp"]

    @property
    def get_type(self) -> str:
        return self["type"]

    @property
    def user_id(self) -> str:
        return self["userId"]

    @property
    def app_id(self) -> str:
        return self["appId"]

    @property
    def cluster_id(self) -> str:
        return self["clusterId"]

    @property
    def body_size(self) -> int:
        return self["bodySize"]


class RabbitMessage(DictWrapper):
    @property
    def basic_properties(self) -> BasicProperties:
        return BasicProperties(self["basicProperties"])

    @property
    def redelivered(self) -> bool:
        return self["redelivered"]

    @property
    def data(self) -> str:
        return self["data"]

    @property
    def decoded_data(self) -> str:
        """Decodes the data as a str"""
        return base64_decode(self.data)

    @property
    def json_data(self) -> Any:
        """Parses the data as json"""
        if self._json_data is None:
            self._json_data = self._json_deserializer(self.decoded_data)
        return self._json_data


class RabbitMQEvent(DictWrapper):
    """Represents a Rabbit MQ event sent to Lambda

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-mq.html
    - https://aws.amazon.com/blogs/compute/using-amazon-mq-for-rabbitmq-as-an-event-source-for-lambda/
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self._rmq_messages_by_queue = {
            key: [RabbitMessage(message) for message in messages]
            for key, messages in self["rmqMessagesByQueue"].items()
        }

    @property
    def event_source(self) -> str:
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the event source"""
        return self["eventSourceArn"]

    @property
    def rmq_messages_by_queue(self) -> Dict[str, List[RabbitMessage]]:
        return self._rmq_messages_by_queue

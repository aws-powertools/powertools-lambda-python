import base64
import json
from typing import Any, Iterator

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class ActiveMQMessage(DictWrapper):
    @property
    def message_id(self) -> str:
        return self["messageID"]

    @property
    def message_type(self) -> str:
        return self["messageType"]

    @property
    def data(self) -> str:
        return self["data"]

    @property
    def decoded_data(self) -> str:
        """Decodes the data as a str"""
        return base64.b64decode(self.data.encode()).decode()

    @property
    def json_data(self) -> Any:
        """Parses the data as json"""
        return json.loads(self.decoded_data)

    @property
    def connection_id(self) -> str:
        return self["connectionId"]

    @property
    def redelivered(self) -> bool:
        return self["redelivered"]

    @property
    def timestamp(self) -> int:
        return self["timestamp"]

    @property
    def broker_in_time(self) -> int:
        return self["brokerInTime"]


class ActiveMQEvent(DictWrapper):
    """Represents an Active MQ event sent to Lambda

    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-mq.html
    - https://aws.amazon.com/blogs/compute/using-amazon-mq-as-an-event-source-for-aws-lambda/
    """

    @property
    def event_source(self) -> str:
        return self["eventSource"]

    @property
    def event_source_arn(self) -> str:
        return self["eventSourceArn"]

    @property
    def messages(self) -> Iterator[ActiveMQMessage]:
        for record in self["messages"]:
            yield ActiveMQMessage(record)

    @property
    def message(self) -> ActiveMQMessage:
        return next(self.messages)

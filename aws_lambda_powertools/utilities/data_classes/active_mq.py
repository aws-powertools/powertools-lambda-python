import base64
import json
from typing import Any, Iterator, Optional

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

    @property
    def broker_out_time(self) -> int:
        return self["brokerOutTime"]

    @property
    def destination_physicalname(self) -> str:
        return self["destination"]["physicalname"]

    @property
    def delivery_mode(self) -> Optional[int]:
        return self.get("deliveryMode")

    @property
    def correlation_id(self) -> Optional[str]:
        return self.get("correlationID")

    @property
    def reply_to(self) -> Optional[str]:
        return self.get("replyTo")

    @property
    def get_type(self) -> Optional[str]:
        return self.get("type")

    @property
    def expiration(self) -> Optional[int]:
        return self.get("expiration")

    @property
    def priority(self) -> Optional[int]:
        return self.get("priority")


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

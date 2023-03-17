import base64
import json
from typing import Any, Iterator, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class ActiveMQMessage(DictWrapper):
    @property
    def message_id(self) -> str:
        """Unique identifier for the message"""
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
        if self._json_data is None:
            self._json_data = json.loads(self.decoded_data)
        return self._json_data

    @property
    def connection_id(self) -> str:
        return self["connectionId"]

    @property
    def redelivered(self) -> bool:
        """true if the message is being resent to the consumer"""
        return self["redelivered"]

    @property
    def timestamp(self) -> int:
        """Time in milliseconds."""
        return self["timestamp"]

    @property
    def broker_in_time(self) -> int:
        """Time stamp (in milliseconds) for when the message arrived at the broker."""
        return self["brokerInTime"]

    @property
    def broker_out_time(self) -> int:
        """Time stamp (in milliseconds) for when the message left the broker."""
        return self["brokerOutTime"]

    @property
    def properties(self) -> dict:
        """Custom properties"""
        return self["properties"]

    @property
    def destination_physicalname(self) -> str:
        return self["destination"]["physicalname"]

    @property
    def delivery_mode(self) -> Optional[int]:
        """persistent or non-persistent delivery"""
        return self.get("deliveryMode")

    @property
    def correlation_id(self) -> Optional[str]:
        """User defined correlation id"""
        return self.get("correlationID")

    @property
    def reply_to(self) -> Optional[str]:
        """User defined reply to"""
        return self.get("replyTo")

    @property
    def get_type(self) -> Optional[str]:
        """User defined message type"""
        return self.get("type")

    @property
    def expiration(self) -> Optional[int]:
        """Expiration attribute whose value is given in milliseconds"""
        return self.get("expiration")

    @property
    def priority(self) -> Optional[int]:
        """
        JMS defines a ten-level priority value, with 0 as the lowest priority and 9
        as the highest. In addition, clients should consider priorities 0-4 as
        gradations of normal priority and priorities 5-9 as gradations of expedited
        priority.

        JMS does not require that a provider strictly implement priority ordering
        of messages; however, it should do its best to deliver expedited messages
        ahead of normal messages.
        """
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
        """The Amazon Resource Name (ARN) of the event source"""
        return self["eventSourceArn"]

    @property
    def messages(self) -> Iterator[ActiveMQMessage]:
        for record in self["messages"]:
            yield ActiveMQMessage(record)

    @property
    def message(self) -> ActiveMQMessage:
        return next(self.messages)

from __future__ import annotations

from functools import cached_property
from typing import Any, Iterator

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.shared_functions import base64_decode


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
        return base64_decode(self.data)

    @cached_property
    def json_data(self) -> Any:
        return self._json_deserializer(self.decoded_data)

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
        return self["destination"]["physicalName"]

    @property
    def delivery_mode(self) -> int | None:
        """persistent or non-persistent delivery"""
        return self.get("deliveryMode")

    @property
    def correlation_id(self) -> str | None:
        """User defined correlation id"""
        return self.get("correlationID")

    @property
    def reply_to(self) -> str | None:
        """User defined reply to"""
        return self.get("replyTo")

    @property
    def get_type(self) -> str | None:
        """User defined message type"""
        return self.get("type")

    @property
    def expiration(self) -> int | None:
        """Expiration attribute whose value is given in milliseconds"""
        return self.get("expiration")

    @property
    def priority(self) -> int | None:
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

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._messages: Iterator[ActiveMQMessage] | None = None

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
            yield ActiveMQMessage(record, json_deserializer=self._json_deserializer)

    @property
    def message(self) -> ActiveMQMessage:
        """
        Returns the next ActiveMQ message using an iterator

        Returns
        -------
        ActiveMQMessage
            The next activemq message.

        Raises
        ------
        StopIteration
            If there are no more records available.

        """
        if self._messages is None:
            self._messages = self.messages
        return next(self._messages)

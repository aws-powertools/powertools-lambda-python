from typing import Any, Dict, Iterator


class SNSMessageAttribute:
    def __init__(self, message_attribute: Dict[str, str]):
        self._v = message_attribute

    @property
    def get_type(self) -> str:
        """The supported message attribute data types are String, String.Array, Number, and Binary."""
        # Note: this name conflicts with existing python builtins
        return self._v["Type"]

    @property
    def value(self) -> str:
        """The user-specified message attribute value."""
        return self._v["Value"]


class SNSMessage:
    def __init__(self, message: Dict[str, Any]):
        self._v = message

    @property
    def signature_version(self) -> str:
        """Version of the Amazon SNS signature used."""
        return self._v["Sns"]["SignatureVersion"]

    @property
    def timestamp(self) -> str:
        """The time (GMT) when the subscription confirmation was sent."""
        return self._v["Sns"]["Timestamp"]

    @property
    def signature(self) -> str:
        """Base64-encoded "SHA1withRSA" signature of the Message, MessageId, Type, Timestamp, and TopicArn values."""
        return self._v["Sns"]["Signature"]

    @property
    def signing_cert_url(self) -> str:
        """The URL to the certificate that was used to sign the message."""
        return self._v["Sns"]["SigningCertUrl"]

    @property
    def message_id(self) -> str:
        """A Universally Unique Identifier, unique for each message published.

        For a message that Amazon SNS resends during a retry, the message ID of the original message is used."""
        return self._v["Sns"]["MessageId"]

    @property
    def message(self) -> str:
        """A string that describes the message. """
        return self._v["Sns"]["Message"]

    @property
    def message_attributes(self) -> Dict[str, SNSMessageAttribute]:
        return {k: SNSMessageAttribute(v) for (k, v) in self._v["Sns"]["MessageAttributes"].items()}

    @property
    def get_type(self) -> str:
        """The type of message.

        For a subscription confirmation, the type is SubscriptionConfirmation."""
        # Note: this name conflicts with existing python builtins
        return self._v["Sns"]["Type"]

    @property
    def unsubscribe_url(self) -> str:
        """A URL that you can use to unsubscribe the endpoint from this topic.

        If you visit this URL, Amazon SNS unsubscribes the endpoint and stops sending notifications to this endpoint."""
        return self._v["Sns"]["UnsubscribeUrl"]

    @property
    def topic_arn(self) -> str:
        """The Amazon Resource Name (ARN) for the topic that this endpoint is subscribed to."""
        return self._v["Sns"]["TopicArn"]

    @property
    def subject(self) -> str:
        """The Subject parameter specified when the notification was published to the topic."""
        return self._v["Sns"]["Subject"]


class SNSEventRecord:
    def __init__(self, record: Dict[str, Any]):
        self._v = record

    @property
    def event_version(self) -> str:
        """Event version"""
        return self._v["EventVersion"]

    @property
    def event_subscription_arn(self) -> str:
        return self._v["EventSubscriptionArn"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the SNS event record originated. For SNS, this is aws:sns"""
        return self._v["EventSource"]

    @property
    def sns(self) -> SNSMessage:
        return SNSMessage(self._v)


class SNSEvent(dict):
    """SNS Event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
    """

    @property
    def records(self) -> Iterator[SNSEventRecord]:
        for record in self["Records"]:
            yield SNSEventRecord(record)

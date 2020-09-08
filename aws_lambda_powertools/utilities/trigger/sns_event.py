from typing import Dict, Iterator


class SNSMessageAttribute(dict):
    @property
    def get_type(self) -> str:
        """Get the `type` property"""
        # Note: this name conflicts with existing python builtins
        return self["Type"]

    @property
    def value(self) -> str:
        return self["Value"]


class SNSMessage(dict):
    @property
    def signature_version(self) -> str:
        return self["SignatureVersion"]

    @property
    def timestamp(self) -> str:
        return self["Timestamp"]

    @property
    def signature(self) -> str:
        return self["Signature"]

    @property
    def signing_cert_url(self) -> str:
        return self["SigningCertUrl"]

    @property
    def message_id(self) -> str:
        return self["MessageId"]

    @property
    def message(self) -> str:
        return self["Message"]

    @property
    def message_attributes(self) -> Dict[str, SNSMessageAttribute]:
        return {k: SNSMessageAttribute(v) for (k, v) in self["MessageAttributes"].items()}

    @property
    def get_type(self) -> str:
        """Get the `type` property"""
        # Note: this name conflicts with existing python builtins
        return self["Type"]

    @property
    def unsubscribe_url(self) -> str:
        return self["UnsubscribeUrl"]

    @property
    def topic_arn(self) -> str:
        return self["TopicArn"]

    @property
    def subject(self) -> str:
        return self["Subject"]


class SNSEventRecord(dict):
    @property
    def event_version(self) -> str:
        return self["EventVersion"]

    @property
    def event_subscription_arn(self) -> str:
        return self["EventSubscriptionArn"]

    @property
    def event_source(self) -> str:
        return self["EventSource"]

    @property
    def sns(self) -> SNSMessage:
        return SNSMessage(self["Sns"])


class SNSEvent(dict):
    """SNS Event

    Documentation: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
    """

    @property
    def records(self) -> Iterator[SNSEventRecord]:
        for record in self["Records"]:
            yield SNSEventRecord(record)

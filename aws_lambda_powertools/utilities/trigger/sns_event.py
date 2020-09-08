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
        return self["Sns"]["SignatureVersion"]

    @property
    def timestamp(self) -> str:
        return self["Sns"]["Timestamp"]

    @property
    def signature(self) -> str:
        return self["Sns"]["Signature"]

    @property
    def signing_cert_url(self) -> str:
        return self["Sns"]["SigningCertUrl"]

    @property
    def message_id(self) -> str:
        return self["Sns"]["MessageId"]

    @property
    def message(self) -> str:
        return self["Sns"]["Message"]

    @property
    def message_attributes(self) -> Dict[str, SNSMessageAttribute]:
        return {k: SNSMessageAttribute(v) for (k, v) in self["Sns"]["MessageAttributes"].items()}

    @property
    def get_type(self) -> str:
        """Get the `type` property"""
        # Note: this name conflicts with existing python builtins
        return self["Sns"]["Type"]

    @property
    def unsubscribe_url(self) -> str:
        return self["Sns"]["UnsubscribeUrl"]

    @property
    def topic_arn(self) -> str:
        return self["Sns"]["TopicArn"]

    @property
    def subject(self) -> str:
        return self["Sns"]["Subject"]


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
        return SNSMessage(self)


class SNSEvent(dict):
    """SNS Event

    Documentation: https://docs.aws.amazon.com/lambda/latest/dg/with-sns.html
    """

    @property
    def records(self) -> Iterator[SNSEventRecord]:
        for record in self["Records"]:
            yield SNSEventRecord(record)

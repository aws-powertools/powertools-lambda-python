from typing import List, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class WorkMailEnvelope(DictWrapper):
    @property
    def mail_from(self) -> str:
        """The From address, which is usually the email address of the user who sent the email message.

        If the user sent the email message as another user or on behalf of another user, the mailFrom field returns
        the email address of the user on whose behalf the email message was sent, not the email address of the
        actual sender."""
        return self["mailFrom"]["address"]

    @property
    def recipients(self) -> List[str]:
        """A list of recipient email addresses. There is no distinction between To, CC, or BCC."""
        return [recipient["address"] for recipient in self["recipients"]]


class WorkMailEvent(DictWrapper):
    """Amazon WorkMail event trigger

    NOTE: For synchronous calls Lambda functions must respond within 15 seconds, or be treated as failed invocations.

    Documentation:
    --------------
    - https://docs.aws.amazon.com/workmail/latest/adminguide/lambda.html
    """

    @property
    def summary_version(self) -> str:
        """The version number for LambdaEventData.

        Only updates when a backwards incompatible change is made in LambdaEventData."""
        return self["summaryVersion"]

    @property
    def envelope(self) -> WorkMailEnvelope:
        """The envelope of the email message"""
        return WorkMailEnvelope(self["envelope"])

    @property
    def sender(self) -> Optional[str]:
        """The email address of the user who sent the email message on behalf of another user.

        This field is set only when an email message is sent on behalf of another user."""
        _sender = self.get("sender")
        if _sender:
            return _sender.get("address")
        return None

    @property
    def subject(self) -> Optional[str]:
        """The email address of the user who sent the email message on behalf of another user.

        This field is set only when an email message is sent on behalf of another user."""
        return self.get("subject")

    @property
    def message_id(self) -> str:
        """A unique ID used to access the full content of the email message when using the
        Amazon WorkMail Message Flow SDK."""
        return self["messageId"]

    @property
    def invocation_id(self) -> str:
        """The ID for a unique Lambda invocation.

        This ID remains the same when a Lambda function is called more than once for the same LambdaEventData.
        Use to detect retries and avoid duplication."""
        return self["invocationId"]

    @property
    def flow_direction(self) -> str:
        """Indicates the direction of the email flow, either INBOUND or OUTBOUND."""
        return self["flowDirection"]

    @property
    def truncated(self) -> bool:
        """Applies to the payload size, not the subject line length.

        When true, the payload size exceeds the 128 KB limit, so the list of recipients is
        truncated in order to meet the limit."""
        return self["truncated"]

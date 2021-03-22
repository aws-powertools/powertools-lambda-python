from enum import Enum, auto
from typing import Dict, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class ConnectContactFlowChannel(Enum):
    VOICE = auto()
    CHAT = auto()


class ConnectContactFlowEndpointType(Enum):
    TELEPHONE_NUMBER = auto()


class ConnectContactFlowInitiationMethod(Enum):
    INBOUND = auto()
    OUTBOUND = auto()
    TRANSFER = auto()
    CALLBACK = auto()
    API = auto()


class ConnectContactFlowEndpoint(DictWrapper):
    @property
    def address(self) -> str:
        """The phone number."""
        return self["Address"]

    @property
    def endpoint_type(self) -> ConnectContactFlowEndpointType:
        """The endpoint type."""
        return ConnectContactFlowEndpointType[self["Type"]]


class ConnectContactFlowQueue(DictWrapper):
    @property
    def arn(self) -> str:
        """The unique queue ARN."""
        return self["ARN"]

    @property
    def name(self) -> str:
        """The queue name."""
        return self["Name"]


class ConnectContactFlowMediaStreamAudio(DictWrapper):
    @property
    def start_fragment_number(self) -> Optional[str]:
        """The number that identifies the Kinesis Video Streams fragment, in the stream used for Live media streaming,
        in which the customer audio stream started.
        """
        return self["StartFragmentNumber"]

    @property
    def start_timestamp(self) -> Optional[str]:
        """When the customer audio stream started."""
        return self["StartTimestamp"]

    @property
    def stream_arn(self) -> Optional[str]:
        """The ARN of the Kinesis Video stream used for Live media streaming that includes the customer data to
        reference.
        """
        return self["StreamARN"]


class ConnectContactFlowMediaStreamCustomer(DictWrapper):
    @property
    def audio(self) -> ConnectContactFlowMediaStreamAudio:
        return ConnectContactFlowMediaStreamAudio(self["Audio"])


class ConnectContactFlowMediaStreams(DictWrapper):
    @property
    def customer(self) -> ConnectContactFlowMediaStreamCustomer:
        return ConnectContactFlowMediaStreamCustomer(self["Customer"])


class ConnectContactFlowData(DictWrapper):
    @property
    def attributes(self) -> Dict[str, str]:
        """These are attributes that have been previously associated with a contact,
        such as when using a Set contact attributes block in a contact flow.
        This map may be empty if there aren't any saved attributes.
        """
        return self["Attributes"]

    @property
    def channel(self) -> ConnectContactFlowChannel:
        """The method used to contact your contact center."""
        return ConnectContactFlowChannel[self["Channel"]]

    @property
    def contact_id(self) -> str:
        """The unique identifier of the contact."""
        return self["ContactId"]

    @property
    def customer_endpoint(self) -> Optional[ConnectContactFlowEndpoint]:
        """Contains the customer’s address (number) and type of address."""
        if self["CustomerEndpoint"] is not None:
            return ConnectContactFlowEndpoint(self["CustomerEndpoint"])
        return None

    @property
    def initial_contact_id(self) -> str:
        """The unique identifier for the contact associated with the first interaction between the customer and your
        contact center. Use the initial contact ID to track contacts between contact flows.
        """
        return self["InitialContactId"]

    @property
    def initiation_method(self) -> ConnectContactFlowInitiationMethod:
        """How the contact was initiated."""
        return ConnectContactFlowInitiationMethod[self["InitiationMethod"]]

    @property
    def instance_arn(self) -> str:
        """The ARN for your Amazon Connect instance."""
        return self["InstanceARN"]

    @property
    def previous_contact_id(self) -> str:
        """The unique identifier for the contact before it was transferred.
        Use the previous contact ID to trace contacts between contact flows.
        """
        return self["PreviousContactId"]

    @property
    def queue(self) -> Optional[ConnectContactFlowQueue]:
        """The current queue."""
        if self["Queue"] is not None:
            return ConnectContactFlowQueue(self["Queue"])
        return None

    @property
    def system_endpoint(self) -> Optional[ConnectContactFlowEndpoint]:
        """Contains the address (number) the customer dialed to call your contact center and type of address."""
        if self["SystemEndpoint"] is not None:
            return ConnectContactFlowEndpoint(self["SystemEndpoint"])
        return None

    @property
    def media_streams(self) -> ConnectContactFlowMediaStreams:
        return ConnectContactFlowMediaStreams(self["MediaStreams"])


class ConnectContactFlowEvent(DictWrapper):
    """Amazon Connect contact flow event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/connect/latest/adminguide/connect-lambda-functions.html
    """

    @property
    def contact_data(self) -> ConnectContactFlowData:
        """This is always passed by Amazon Connect for every contact. Some parameters are optional."""
        return ConnectContactFlowData(self["Details"]["ContactData"])

    @property
    def parameters(self) -> Dict[str, str]:
        """These are parameters specific to this call that were defined when you created the Lambda function."""
        return self["Details"]["Parameters"]

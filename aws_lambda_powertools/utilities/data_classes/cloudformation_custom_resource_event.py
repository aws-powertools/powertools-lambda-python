from enum import Enum
from typing import Any, Dict, Optional

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CloudFormationRequestType(Enum):
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"


class CloudFormationCustomResourceEvent(DictWrapper):
    @property
    def request_type(self) -> CloudFormationRequestType:
        return CloudFormationRequestType(self["RequestType"])

    @property
    def service_token(self) -> str:
        return self["ServiceToken"]

    @property
    def response_url(self) -> str:
        return self["ResponseUrl"]

    @property
    def stack_id(self) -> str:
        return self["StackId"]

    @property
    def request_id(self) -> str:
        return self["RequestId"]

    @property
    def logical_resource_id(self) -> str:
        return self["LogicalResourceId"]

    @property
    def physical_resource_id(self) -> Optional[str]:
        return self.get("PhysicalResourceId")

    @property
    def resource_type(self) -> str:
        return self["ResourceType"]

    @property
    def resource_properties(self) -> Optional[Dict[str, Any]]:
        return self.get("ResourceProperties")

    @property
    def old_resource_properties(self) -> Optional[Dict[str, Any]]:
        return self.get("OldResourceProperties")

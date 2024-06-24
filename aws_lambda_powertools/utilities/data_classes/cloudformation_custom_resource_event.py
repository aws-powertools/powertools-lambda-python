from typing import Any, Dict, Literal

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class CloudFormationCustomResourceEvent(DictWrapper):
    @property
    def request_type(self) -> Literal["Create", "Update", "Delete"]:
        return self["RequestType"]

    @property
    def service_token(self) -> str:
        return self["ServiceToken"]

    @property
    def response_url(self) -> str:
        return self["ResponseURL"]

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
    def physical_resource_id(self) -> str:
        return self.get("PhysicalResourceId") or ""

    @property
    def resource_type(self) -> str:
        return self["ResourceType"]

    @property
    def resource_properties(self) -> Dict[str, Any]:
        return self.get("ResourceProperties") or {}

    @property
    def old_resource_properties(self) -> Dict[str, Any]:
        return self.get("OldResourceProperties") or {}

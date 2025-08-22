from typing import Dict, Type, Union

from pydantic import BaseModel, Field


class VpcLatticeModel(BaseModel):
    method: str = Field(
        description="The HTTP method used for the request.",
        examples=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    raw_path: str = Field(
        description="The raw path portion of the request URL.",
        examples=["/testpath", "/api/v1/users", "/health"],
    )
    body: Union[str, Type[BaseModel]] = Field(
        description="The request body. Can be a string or a parsed model if content-type allows parsing.",
    )
    is_base64_encoded: bool = Field(description="Indicates whether the body is base64-encoded.", examples=[True, False])
    headers: Dict[str, str] = Field(
        description="The request headers as key-value pairs.",
        examples=[
            {"host": "test-lambda-service.vpc-lattice-svcs.us-east-2.on.aws", "user-agent": "curl/7.64.1"},
            {"content-type": "application/json"},
        ],
    )
    query_string_parameters: Dict[str, str] = Field(
        description="The query string parameters as key-value pairs.",
        examples=[{"order-id": "1"}, {"page": "2", "limit": "10"}],
    )

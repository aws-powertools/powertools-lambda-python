from typing import Literal

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress


class TransferFamilyAuthorizer(BaseModel):
    username: str = Field(
        description="The username of the user attempting to authenticate.",
        examples=["bobusa", "john.doe", "sftp-user-123", "data-transfer-user"],
    )
    password: str | None = Field(
        default=None,
        description="The password for authentication.",
        examples=["<password>", "<user-password>", None],
    )
    protocol: Literal["SFTP", "FTP", "FTPS"] = Field(
        description="The protocol used for the connection.",
        examples=["SFTP", "FTPS", "FTP"],
    )
    server_id: str = Field(
        ...,
        alias="serverId",
        description="The server ID of the Transfer Family server.",
        examples=["s-abcd123456", "s-1234567890abcdef0", "s-example123"],
    )
    source_ip: IPvAnyAddress = Field(
        ...,
        alias="sourceIp",
        description="The IP address of the client connecting to the Transfer Family server.",
    )

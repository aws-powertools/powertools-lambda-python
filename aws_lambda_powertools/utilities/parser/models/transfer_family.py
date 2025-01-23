from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic.networks import IPvAnyAddress


class TransferFamilyAuthorizer(BaseModel):
    username: str
    password: Optional[str] = None
    protocol: Literal["SFTP", "FTP", "FTPS"]
    server_id: str = Field(..., alias="serverId")
    source_ip: IPvAnyAddress = Field(..., alias="sourceIp")

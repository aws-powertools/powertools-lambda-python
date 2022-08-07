from typing import Dict

from pydantic import BaseModel, Field


class AssetTemplateConfigSource(BaseModel):
    path: str
    packaging: str


class AssetTemplateConfigDestinationsAccount(BaseModel):
    bucket_name: str = Field(str, alias="bucketName")
    object_key: str = Field(str, alias="objectKey")
    assume_role_arn: str = Field(str, alias="assumeRoleArn")


class AssetTemplateConfigDestinations(BaseModel):
    current_account_current_region: AssetTemplateConfigDestinationsAccount = Field(
        AssetTemplateConfigDestinationsAccount, alias="current_account-current_region"
    )


class AssetTemplateConfig(BaseModel):
    source: AssetTemplateConfigSource
    destinations: AssetTemplateConfigDestinations


class TemplateAssembly(BaseModel):
    version: str
    files: Dict[str, AssetTemplateConfig]
    docker_images: Dict = Field(Dict, alias="dockerImages")

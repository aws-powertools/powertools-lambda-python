import io
import json
import zipfile
from pathlib import Path
from typing import List, Optional

import boto3
import botocore.exceptions
from mypy_boto3_s3 import S3Client

from aws_lambda_powertools import Logger
from tests.e2e.utils.models import AssetTemplateConfig, TemplateAssembly

logger = Logger(service="e2e-utils")


class Asset:
    def __init__(
        self, config: AssetTemplateConfig, account_id: str, region: str, boto3_client: Optional[S3Client] = None
    ) -> None:
        """CDK Asset logic to verify existence and resolve deeply nested configuration

        Parameters
        ----------
        config : AssetTemplateConfig
            CDK Asset configuration found in synthesized template
        account_id : str
            AWS Account ID
        region : str
            AWS Region
        boto3_client : Optional[&quot;S3Client&quot;], optional
            S3 client instance for asset operations, by default None
        """
        self.config = config
        self.s3 = boto3_client or boto3.client("s3")
        self.account_id = account_id
        self.region = region
        self.asset_path = config.source.path
        self.asset_packaging = config.source.packaging
        self.object_key = config.destinations.current_account_current_region.object_key
        self._bucket = config.destinations.current_account_current_region.bucket_name
        self.bucket_name = self._resolve_bucket_name()

    @property
    def is_zip(self):
        return self.asset_packaging == "zip"

    def exists_in_s3(self, key: str) -> bool:
        try:
            return self.s3.head_object(Bucket=self.bucket_name, Key=key) is not None
        except botocore.exceptions.ClientError:
            return False

    def _resolve_bucket_name(self) -> str:
        return self._bucket.replace("${AWS::AccountId}", self.account_id).replace("${AWS::Region}", self.region)


class Assets:
    def __init__(
        self, asset_manifest: Path, account_id: str, region: str, boto3_client: Optional[S3Client] = None
    ) -> None:
        """CDK Assets logic to find each asset, compress, and upload

        Parameters
        ----------
        asset_manifest : Path
            Asset manifest JSON file (self.__synthesize)
        account_id : str
            AWS Account ID
        region : str
            AWS Region
        boto3_client : Optional[S3Client], optional
            S3 client instance for asset operations, by default None
        """
        self.asset_manifest = asset_manifest
        self.account_id = account_id
        self.region = region
        self.s3 = boto3_client or boto3.client("s3")
        self.assets = self._find_assets_from_template()
        self.assets_location = str(self.asset_manifest.parent)

    def upload(self):
        """Drop-in replacement for cdk-assets package s3 upload part.
        https://www.npmjs.com/package/cdk-assets.
        We use custom solution to avoid dependencies from nodejs ecosystem.
        We follow the same design cdk-assets:
        https://github.com/aws/aws-cdk-rfcs/blob/master/text/0092-asset-publishing.md.
        """
        for asset in self.assets:
            if not asset.is_zip:
                logger.debug(f"Asset '{asset.object_key}' is not zip. Skipping upload.")
                continue

            if asset.exists_in_s3(key=asset.object_key):
                logger.debug(f"Asset '{asset.object_key}' already exists in S3. Skipping upload.")
                continue

            archive = self._compress_assets(asset)
            logger.debug("Uploading archive to S3")
            self.s3.upload_fileobj(Fileobj=archive, Bucket=asset.bucket_name, Key=asset.object_key)
            logger.debug("Successfully uploaded")

    def _find_assets_from_template(self) -> List[Asset]:
        data = json.loads(self.asset_manifest.read_text())
        template = TemplateAssembly(**data)
        return [
            Asset(config=asset_config, account_id=self.account_id, region=self.region)
            for asset_config in template.files.values()
        ]

    def _compress_assets(self, asset: Asset) -> io.BytesIO:
        buf = io.BytesIO()
        asset_dir = f"{self.assets_location}/{asset.asset_path}"
        asset_files = list(Path(asset_dir).iterdir())
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for asset_file in asset_files:
                logger.debug(f"Adding file '{asset_file}' to the archive.")
                archive.write(asset_file, arcname=asset_file.relative_to(asset_dir))
        buf.seek(0)
        return buf

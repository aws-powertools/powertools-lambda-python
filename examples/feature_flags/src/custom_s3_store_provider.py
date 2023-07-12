import json
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from aws_lambda_powertools.utilities.feature_flags.base import StoreProvider
from aws_lambda_powertools.utilities.feature_flags.exceptions import (
    ConfigurationStoreError,
)


class S3StoreProvider(StoreProvider):
    def __init__(self, bucket_name: str, object_key: str):
        # Initialize the client to your custom store provider

        super().__init__()

        self.bucket_name = bucket_name
        self.object_key = object_key
        self.client = boto3.client("s3")

    def _get_s3_object(self) -> Dict[str, Any]:
        # Retrieve the object content
        parameters = {"Bucket": self.bucket_name, "Key": self.object_key}

        try:
            response = self.client.get_object(**parameters)
            return json.loads(response["Body"].read().decode())
        except ClientError as exc:
            raise ConfigurationStoreError("Unable to get S3 Store Provider configuration file") from exc

    def get_configuration(self) -> Dict[str, Any]:
        return self._get_s3_object()

    @property
    def get_raw_configuration(self) -> Dict[str, Any]:
        return self._get_s3_object()

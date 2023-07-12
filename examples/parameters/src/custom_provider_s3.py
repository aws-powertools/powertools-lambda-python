import copy
from typing import Dict

import boto3

from aws_lambda_powertools.utilities.parameters import BaseProvider


class S3Provider(BaseProvider):
    def __init__(self, bucket_name: str):
        # Initialize the client to your custom parameter store
        # E.g.:

        super().__init__()

        self.bucket_name = bucket_name
        self.client = boto3.client("s3")

    def _get(self, name: str, **sdk_options) -> str:
        # Retrieve a single value
        # E.g.:

        sdk_options["Bucket"] = self.bucket_name
        sdk_options["Key"] = name

        response = self.client.get_object(**sdk_options)
        return response["Body"].read().decode()

    def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
        # Retrieve multiple values
        # E.g.:

        list_sdk_options = copy.deepcopy(sdk_options)

        list_sdk_options["Bucket"] = self.bucket_name
        list_sdk_options["Prefix"] = path

        list_response = self.client.list_objects_v2(**list_sdk_options)

        parameters = {}

        for obj in list_response.get("Contents", []):
            get_sdk_options = copy.deepcopy(sdk_options)

            get_sdk_options["Bucket"] = self.bucket_name
            get_sdk_options["Key"] = obj["Key"]

            get_response = self.client.get_object(**get_sdk_options)

            parameters[obj["Key"]] = get_response["Body"].read().decode()

        return parameters

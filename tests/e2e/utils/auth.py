from urllib.parse import urlparse

import boto3
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth


def build_iam_auth(url: str, aws_service: str) -> BotoAWSRequestsAuth:
    """Generates IAM auth keys for a given hostname and service.
    This can be directly passed on to the requests library to authenticate the request.
    """
    hostname = urlparse(url).hostname
    region = boto3.Session().region_name
    return BotoAWSRequestsAuth(aws_host=hostname, aws_region=region, aws_service=aws_service)

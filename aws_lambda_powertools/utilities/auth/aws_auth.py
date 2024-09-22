from __future__ import annotations

import json
import os
from enum import Enum
from typing import Optional

import botocore.session
from botocore import crt
from botocore.awsrequest import AWSRequest


class ServicePrefix(Enum):
    """
    AWS Service Prefixes - Enumerations of the supported service proxy types
    URLs:
        https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html
    """

    LATTICE = "vpc-lattice-svcs"
    RESTAPI = "execute-api"
    HTTPAPI = "apigateway"
    APPSYNC = "appsync"


class SigV4Auth:
    """
    Authenticating Requests (AWS Signature Version 4)
    Requests that were signed with SigV4 will have SignatureVersion set to AWS4-HMAC-SHA256

    Args:
        url (str): URL
        service (ServicePrefix): AWS service Prefix
        region (str, Optional): AWS region
        body (dict, optional): Request body
        params (dict, optional): Request parameters
        headers (dict, optional): Request headers
        method (str, optional): Request method

    Returns:
        SigV4Auth: SigV4Auth instance

    Examples
    --------
    >>> from aws_lambda_powertools.utilities.auth import SigV4Auth, ServicePrefix
    >>> prepped = SigV4Auth.prepare_request(region="us-east-2", service=ServicePrefix.LATTICE, url="https://test-fake-service.vpc-lattice-svcs.us-east-2.on.aws")
    """

    @staticmethod
    def prepare_request(
        url: str,
        service: ServicePrefix,
        region: Optional[str],
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = "GET",
    ):
        if region is None:
            region = os.environ.get("AWS_REGION")

        if body is not None:
            body = json.dumps(body)
        else:
            body = json.dumps({})

        credentials = botocore.session.Session().get_credentials()

        signer = crt.auth.CrtSigV4Auth(credentials, service.value, region)

        if headers is None:
            headers = {"Content-Type": "application/json"}

        request = AWSRequest(method=method, url=url, data=body, params=params, headers=headers)

        if service.value == "vpc-lattice-svcs":
            # payload signing is not supported for vpc-lattice-svcs
            request.context["payload_signing_enabled"] = False

        signer.add_auth(request)
        return request.prepare()


class SigV4aAuth:
    """
    Authenticating Requests (AWS Signature Version 4a)
    Requests that were signed with SigV4A will have a SignatureVersion set to AWS4-ECDSA-P256-SHA256

    Args:
        url (str): URL
        service (ServicePrefix): AWS service Prefix
        region (str, Optional): AWS region
        body (dict, optional): Request body
        params (dict, optional): Request parameters
        headers (dict, optional): Request headers
        method (str, optional): Request method

    Returns:
        SigV4aAuth: SigV4aAuth instance

    Examples
    --------
    >>> from aws_lambda_powertools.utilities.iam import SigV4aAuth, ServicePrefix
    >>> prepped = SigV4aAuth.prepare_request(region="us-east-2", service=ServicePrefix.LATTICE, url="https://test-fake-service.vpc-lattice-svcs.us-east-2.on.aws")
    """

    @staticmethod
    def prepare_request(
        url: str,
        service: ServicePrefix,
        region: Optional[str] = "*",
        body: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = "GET",
    ):
        if body is not None:
            body = json.dumps(body)
        else:
            body = json.dumps({})

        credentials = botocore.session.Session().get_credentials()

        signer = crt.auth.CrtSigV4AsymAuth(credentials, service.value, region)

        if headers is None:
            headers = {"Content-Type": "application/json"}

        request = AWSRequest(method=method, url=url, data=body, params=params, headers=headers)

        if service.value == "vpc-lattice-svcs":
            # payload signing is not supported for vpc-lattice-svcs
            request.context["payload_signing_enabled"] = False

        signer.add_auth(request)
        return request.prepare()

from __future__ import annotations

from enum import Enum
from typing import Optional

import botocore.session
from botocore import crt
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials, ReadOnlyCredentials


class AWSServicePrefix(Enum):
    """
    AWS Service Prefixes - Enumerations of the supported service proxy types

    URLs:
        https://docs.aws.amazon.com/service-authorization/latest/reference/reference_policies_actions-resources-contextkeys.html
    """

    LATTICE = "vpc-lattice-svcs"
    RESTAPI = "execute-api"
    HTTPAPI = "apigateway"
    APPSYNC = "appsync"


class AWSSigV4Auth:
    """
    Authenticating Requests (AWS Signature Version 4)
    Requests that were signed with SigV4 will have SignatureVersion set to AWS4-HMAC-SHA256

    Args:
        url (str): URL
        region (str): AWS region
        body (str, optional): Request body
        params (dict, optional): Request parameters
        headers (dict, optional): Request headers
        method (str, optional): Request method
        service (str, optional): AWS service
        access_key (str, optional): AWS access key
        secret_key (str, optional): AWS secret key
        token (str, optional): AWS session token

    Returns:
        SigV4Auth: SigV4Auth instance

    Examples
    --------
    **Using default credentials**
    >>> from aws_lambda_powertools.utilities.iam import AWSSigV4Auth
    >>> auth = AWSSigV4Auth(region="us-east-2", service=AWSServicePrefix.LATTICE, url="https://test-fake-service.vpc-lattice-svcs.us-east-2.on.aws")
    """

    def __init__(
        self,
        url: str,
        region: str,
        body: Optional[str] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = "GET",
        service: Enum = AWSServicePrefix.LATTICE,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.service = service.value
        self.region = region
        self.method = method
        self.url = url
        self.data = body
        self.params = params
        self.headers = headers

        self.credentials: Credentials | ReadOnlyCredentials

        if access_key and secret_key and token:
            self.access_key = access_key
            self.secret_key = secret_key
            self.token = token
            self.credentials = Credentials(access_key=self.access_key, secret_key=self.secret_key, token=self.token)
        else:
            credentials = botocore.session.Session().get_credentials()
            self.credentials = credentials.get_frozen_credentials()

        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}

        sigv4 = SigV4Auth(credentials=self.credentials, service_name=self.service, region_name=self.region)

        request = AWSRequest(method=self.method, url=self.url, data=self.data, params=self.params, headers=self.headers)

        if self.service == AWSServicePrefix.LATTICE.value:
            # payload signing is not supported for vpc-lattice-svcs
            request.context["payload_signing_enabled"] = False

        sigv4.add_auth(request)
        self.signed_request = request.prepare()

        def __call__(self):
            return self.signed_request


class AWSSigV4aAuth:
    """
    Authenticating Requests (AWS Signature Version 4a)
    Requests that were signed with SigV4A will have a SignatureVersion set to AWS4-ECDSA-P256-SHA256

    Args:
        url (str): URL
        region (str): AWS region
        body (str, optional): Request body
        params (dict, optional): Request parameters
        headers (dict, optional): Request headers
        method (str, optional): Request method
        service (str, optional): AWS service
        access_key (str, optional): AWS access key
        secret_key (str, optional): AWS secret key
        token (str, optional): AWS session token

    Returns:
        SigV4aAuth: SigV4aAuth instance

    Examples
    --------
    **Using default credentials**
    >>> from aws_lambda_powertools.utilities.iam import AWSSigV4aAuth
    >>> auth = AWSSigV4aAuth(region="us-east-2", service=AWSServicePrefix.LATTICE, url="https://test-fake-service.vpc-lattice-svcs.us-east-2.on.aws")
    """

    def __init__(
        self,
        url: str,
        region: str,
        body: Optional[str] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: Optional[str] = "GET",
        service: Enum = AWSServicePrefix.LATTICE,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.service = service.value
        self.region = region
        self.method = method
        self.url = url
        self.data = body
        self.params = params
        self.headers = headers

        self.credentials: Credentials | ReadOnlyCredentials

        if access_key and secret_key and token:
            self.access_key = access_key
            self.secret_key = secret_key
            self.token = token
            self.credentials = Credentials(access_key=self.access_key, secret_key=self.secret_key, token=self.token)
        else:
            credentials = botocore.session.Session().get_credentials()
            self.credentials = credentials.get_frozen_credentials()

        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}

        signer = crt.auth.CrtSigV4AsymAuth(self.credentials, self.service, self.region)

        request = AWSRequest(method=self.method, url=self.url, data=self.data, params=self.params, headers=self.headers)

        if self.service == AWSServicePrefix.LATTICE.value:
            # payload signing is not supported for vpc-lattice-svcs
            request.context["payload_signing_enabled"] = False

        signer.add_auth(request)
        self.signed_request = request.prepare()

        def __call__(self):
            return self.signed_request

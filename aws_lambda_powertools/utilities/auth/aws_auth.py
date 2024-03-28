from __future__ import annotations

import base64
import json
from enum import Enum
from typing import Optional

import botocore.session
import urllib3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials, ReadOnlyCredentials


def _authorization_header(client_id: str, client_secret: str) -> str:
    """
    Generates the Authorization header for the request

    Args:
        client_id (str): Client ID
        client_secret (str): Client Secret

    Returns:
        str: Base64 encoded Authorization header
    """
    auth_string = f"{client_id}:{client_secret}"
    encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded_auth_string}"


def _get_token(response: dict) -> str:
    """
    Gets the token from the response

    Args:
        response (dict): Response from the authentication endpoint

    Returns:
        str: Token
    """
    if "access_token" in response:
        return response["access_token"]
    elif "id_token" in response:
        return response["id_token"]
    else:
        raise Exception("Unable to get token from response")


def _request_access_token(auth_endpoint: str, body: dict, headers: dict) -> str:
    """
    Gets the token from the Auth0 authentication endpoint

    Args:
        client_id (str): Client ID
        client_secret (str): Client Secret
        audience (str): Audience
        auth_endpoint (str): Auth0 authentication endpoint

    Returns:
        str: Token
    """
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    http = urllib3.PoolManager()

    if isinstance(body, dict):
        json_body = json.dumps(body)
    elif isinstance(body, str):
        json_body = body

    try:
        response = http.request("POST", auth_endpoint, headers=headers, body=json_body)
        response = response.json()
        return _get_token(response)
    except (urllib3.exceptions.RequestError, urllib3.exceptions.HTTPError) as error:
        # If there is an error with the request, handle it here
        # REVIEW: CREATE A CUSTOM EXCEPTION FOR THIS
        raise Exception(error) from error


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


class AuthProvider(Enum):
    """
    Auth Provider - Enumerations of the supported authentication providers
    """

    AUTH0 = "auth0"
    COGNITO = "cognito"
    OKTA = "okta"


class AWSSigV4Auth:
    """
    Authenticating Requests (AWS Signature Version 4)

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


class JWTAuth:

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        auth_endpoint: str,
        provider: Enum = AuthProvider.COGNITO,
        audience: Optional[str] = None,
        scope: Optional[list] = None,
    ):

        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_endpoint = auth_endpoint.removesuffix("/")
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.provider = provider
        self.audience = audience
        self.scope = scope

        self.body = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        if self.provider == AuthProvider.COGNITO.value:

            encoded_auth_string = _authorization_header(self.client_id, self.client_secret)
            self.headers["Authorization"] = f"Basic {encoded_auth_string}"
            self.body["grant_type"] = "client_credentials"
            if self.scope:
                self.body["scope"] = " ".join(self.scope)

        if self.provider == AuthProvider.AUTH0.value:

            self.body["client_id"] = self.client_id
            self.body["client_secret"] = self.client_secret
            self.body["grant_type"] = "client_credentials"
            self.body["audience"] = self.audience

        if self.provider == AuthProvider.OKTA.value:

            encoded_auth_string = _authorization_header(self.client_id, self.client_secret)
            self.headers["Accept"] = "application/json"
            self.headers["Authorization"] = f"Basic {encoded_auth_string}"
            self.headers["Cache-Control"] = "no-cache"

            self.body["grant_type"] = "client_credentials"
            if scope:
                self.body["scope"] = " ".join(self.scope)

        # response = _request_access_token(auth_endpoint=self.auth_endpoint, body=self.body, headers=self.headers) # noqa ERA001

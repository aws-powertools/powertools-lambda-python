
from typing import Optional
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
import botocore.session


class AwsSignedRequest:
    """
    Authenticating Requests (AWS Signature Version 4)

    Args:
        region (str): AWS region
        service (str): AWS service
        access_key (str, optional): AWS access key
        secret_key (str, optional): AWS secret key
        token (str, optional): AWS session token

    Returns:
        SigV4Auth: SigV4Auth instance

    Examples
    --------
    **Using default credentials**
    >>> from aws_lambda_powertools.utilities.iam import SigV4AuthFactory
    >>> auth = SigV4AuthFactory(region="us-east-2", service="vpc-lattice-svcs")
    """


    def __init__(
        self,
        service: str,
        method: str,
        url: str,
        data: Optional[str],
        params: Optional[str],
        headers: Optional[str],
        access_key: Optional[str],
        secret_key: Optional[str],
        region: Optional[str],
        token: Optional[str] = None,
        sign_payload: Optional[bool] = False,
    ):

        self._service = service
        self._method = method
        self._url = url
        self._data = data
        self._params = params
        self._headers = headers

        if not region:
            self._region = botocore.session.Session().get_config_variable("region")
        else:
            self._region = region

        if access_key and secret_key:
            self._access_key = access_key
            self._secret_key = secret_key
            self._token = token
            self._credentials = Credentials(access_key=self._access_key, secret_key=self._secret_key, token=self._token)
        else:
            credentials = botocore.session.Session().get_credentials()
            self._credentials = credentials.get_frozen_credentials()

        def __call__(self):
            request = AWSRequest(method=self._method, url=self._url, data=self._data, params=self._params, headers=self._headers)
            if sign_payload is False:
                request.context["payload_signing_enabled"] = False

            signed_request = SigV4Auth(credentials=self._credentials, service_name=self._service, region_name=self._region).add_auth(request)
            return signed_request.prepare()

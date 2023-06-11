
from typing import Optional
from botocore.auth import SigV4Auth
from botocore.credentials import Credentials
from boto3 import Session


class SigV4AuthFactory:
    """
    SigV4 authentication utility

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
        region: str,
        service: str,
        access_key: Optional[str],
        secret_key: Optional[str],
        token: Optional[str],
    ):
        self._region = region
        self._service = service

        if access_key and secret_key or token:
            self._access_key = access_key
            self._secret_key = secret_key
            self._credentials = Credentials(access_key=self._access_key, secret_key=self._secret_key, token=token)

        else:
            self._credentials = Session().get_credentials()

        def __call__(self):
            return SigV4Auth(credentials=self._credentials, service=self._service, region=self._region)
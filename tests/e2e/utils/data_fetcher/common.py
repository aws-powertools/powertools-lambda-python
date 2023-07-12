from datetime import datetime
from typing import Optional, Tuple

import boto3
import requests
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
from requests import Request, Response
from requests.exceptions import RequestException
from retry import retry


def get_lambda_response(
    lambda_arn: str,
    payload: Optional[str] = None,
    client: Optional[LambdaClient] = None,
) -> Tuple[InvocationResponseTypeDef, datetime]:
    client = client or boto3.client("lambda")
    payload = payload or ""
    execution_time = datetime.utcnow()
    return client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse", Payload=payload), execution_time


@retry(RequestException, delay=2, jitter=1.5, tries=5)
def get_http_response(request: Request) -> Response:
    session = requests.Session()
    result = session.send(request.prepare())
    result.raise_for_status()
    return result

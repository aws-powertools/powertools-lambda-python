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
    raise_on_error: bool = True,
) -> Tuple[InvocationResponseTypeDef, datetime]:
    """Invoke function synchronously

    Parameters
    ----------
    lambda_arn : str
        Lambda function ARN to invoke
    payload : Optional[str], optional
        JSON payload for Lambda invocation, by default None
    client : Optional[LambdaClient], optional
        Boto3 Lambda SDK client, by default None
    raise_on_error : bool, optional
        Whether to raise exception upon invocation error, by default True

    Returns
    -------
    Tuple[InvocationResponseTypeDef, datetime]
        Function response and approximate execution time

    Raises
    ------
    RuntimeError
        Function invocation error details
    """
    client = client or boto3.client("lambda")
    payload = payload or ""
    execution_time = datetime.utcnow()

    response: InvocationResponseTypeDef = client.invoke(
        FunctionName=lambda_arn,
        InvocationType="RequestResponse",
        Payload=payload,
    )
    has_error = response.get("FunctionError", "") == "Unhandled"
    if has_error and raise_on_error:
        error_payload = response["Payload"].read().decode()
        raise RuntimeError(f"Function failed invocation: {error_payload}")

    return client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse", Payload=payload), execution_time


@retry(RequestException, delay=2, jitter=1.5, tries=5)
def get_http_response(request: Request) -> Response:
    session = requests.Session()
    result = session.send(request.prepare())
    result.raise_for_status()
    return result

import functools
import time
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from typing import List, Optional, Tuple

import boto3
import requests
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef
from pydantic import BaseModel
from requests import Request, Response
from requests.exceptions import RequestException
from retry import retry

GetLambdaResponse = Tuple[InvocationResponseTypeDef, datetime]


class GetLambdaResponseOptions(BaseModel):
    lambda_arn: str
    payload: Optional[str] = None
    client: Optional[LambdaClient] = None
    raise_on_error: bool = True

    # Maintenance: Pydantic v2 deprecated it; we should update in v3
    class Config:
        arbitrary_types_allowed = True


def get_lambda_response(
    lambda_arn: str,
    payload: Optional[str] = None,
    client: Optional[LambdaClient] = None,
    raise_on_error: bool = True,
) -> GetLambdaResponse:
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

    return response, execution_time


@retry(RequestException, delay=2, jitter=1.5, tries=5)
def get_http_response(request: Request) -> Response:
    session = requests.Session()
    result = session.send(request.prepare())
    result.raise_for_status()
    return result


def get_lambda_response_in_parallel(
    get_lambda_response_options: List[GetLambdaResponseOptions],
) -> List[GetLambdaResponse]:
    """Invoke functions in parallel

    Parameters
    ----------
    get_lambda_response_options : List[GetLambdaResponseOptions]
        List of options to call get_lambda_response with

    Returns
    -------
    List[GetLambdaResponse]
        Function responses and approximate execution time
    """
    result_list = []
    with ThreadPoolExecutor() as executor:
        running_tasks: List[Future] = []
        for options in get_lambda_response_options:
            # Sleep 0.5, 1, 1.5, ... seconds between each invocation. This way
            # we can guarantee that lambdas are executed in parallel, but they are
            # called in the same "order" as they are passed in, thus guaranteeing that
            # we can assert on the correct output.
            time.sleep(0.5 * len(running_tasks))

            get_lambda_response_callback = functools.partial(get_lambda_response, **options.dict())
            running_tasks.append(
                executor.submit(get_lambda_response_callback),
            )

        executor.shutdown(wait=True)
        result_list.extend(running_task.result() for running_task in running_tasks)

    return result_list

from datetime import datetime
from typing import Optional, Tuple

import boto3
from mypy_boto3_lambda import LambdaClient
from mypy_boto3_lambda.type_defs import InvocationResponseTypeDef


def get_lambda_response(
    lambda_arn: str, payload: Optional[str] = None, client: Optional[LambdaClient] = None
) -> Tuple[InvocationResponseTypeDef, datetime]:
    client = client or boto3.client("lambda")
    payload = payload or ""
    execution_time = datetime.utcnow()
    return client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse", Payload=payload), execution_time

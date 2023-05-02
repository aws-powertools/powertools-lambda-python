import os

import boto3
from botocore.response import StreamingBody

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

BUCKET = os.getenv("BUCKET_NAME", "")
REPORT_KEY = os.getenv("REPORT_KEY", "")

tracer = Tracer()
logger = Logger()

session = boto3.Session()
s3 = session.client("s3")


@tracer.capture_method(capture_response=False)
def fetch_payment_report(payment_id: str) -> StreamingBody:
    ret = s3.get_object(Bucket=BUCKET, Key=f"{REPORT_KEY}/{payment_id}")
    logger.debug("Returning streaming body from S3 object....")
    return ret["body"]


@tracer.capture_lambda_handler(capture_response=False)
def lambda_handler(event: dict, context: LambdaContext) -> str:
    payment_id = event.get("payment_id", "")
    report = fetch_payment_report(payment_id=payment_id)
    return report.read().decode()

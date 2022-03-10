import boto3

from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method(capture_response=False)
def get_s3_object(bucket_name, object_key):
    s3 = boto3.client("s3")
    s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
    return s3_object

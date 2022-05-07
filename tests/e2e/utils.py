import io
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Optional, Union

import boto3
from pydantic import BaseModel
from retry import retry


class Log(BaseModel):
    level: str
    location: str
    message: Union[dict, str]
    timestamp: str
    service: str
    cold_start: Optional[bool]
    function_name: Optional[str]
    function_memory_size: Optional[str]
    function_arn: Optional[str]
    function_request_id: Optional[str]
    xray_trace_id: Optional[str]
    extra_info: Optional[str]


@retry(ValueError, delay=1, jitter=1, tries=5)
def get_logs(lambda_function_name: str, log_client: Any, start_time: int):
    response = log_client.filter_log_events(logGroupName=f"/aws/lambda/{lambda_function_name}", startTime=start_time)
    if not response["events"]:
        raise ValueError("Empty response from Cloudwatch Logs. Repeating...")
    filtered_logs = []
    for event in response["events"]:
        try:
            message = Log(**json.loads(event["message"]))
        except json.decoder.JSONDecodeError:
            continue
        filtered_logs.append(message)

    return filtered_logs


def trigger_lambda(lambda_arn):
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(FunctionName=lambda_arn, InvocationType="RequestResponse")
    return response


def find_handlers(directory):
    handlers = []
    for _, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filename = Path(file).stem
                handlers.append(filename)
    print("handlers", handlers)
    return handlers


@retry(ValueError, delay=1, jitter=1, tries=5)
def get_metrics(namespace, cw_client, start_date, end_date, metric_name, service_name):

    response = cw_client.get_metric_data(
        MetricDataQueries=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": namespace,
                        "MetricName": metric_name,
                        "Dimensions": [{"Name": "service", "Value": service_name}],
                    },
                    "Period": 600,
                    "Stat": "Maximum",
                },
                "ReturnData": True,
            },
        ],
        StartTime=start_date,
        EndTime=end_date,
    )

    result = response["MetricDataResults"][0]
    if not result["Values"]:
        raise ValueError("Empty response from Cloudwatch. Repeating...")
    return result


@retry(ValueError, delay=2, jitter=0.5, tries=10)
def get_traces(lambda_function_name: str, xray_client, start_date, end_date):
    paginator = xray_client.get_paginator("get_trace_summaries")
    response_iterator = paginator.paginate(
        StartTime=start_date,
        EndTime=end_date,
        TimeRangeType="Event",
        Sampling=False,
        FilterExpression=f'service("{lambda_function_name}")',
    )

    traces = [trace["TraceSummaries"][0]["Id"] for trace in response_iterator if trace["TraceSummaries"]]
    if not traces:
        raise ValueError("Empty response from X-RAY. Repeating...")

    trace_details = xray_client.batch_get_traces(
        TraceIds=traces,
    )

    return trace_details


def get_all_file_paths(directory):
    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            file_paths.append(os.path.join(root, filename))
    return file_paths


def upload_assets(template, asset_root_dir):
    s3_client = boto3.client("s3")
    s3_resource = boto3.resource("s3")
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    region = boto3.Session().region_name
    assets = find_assets(template, account_id, region)

    for s3_key, bucket in assets.items():
        s3_bucket = s3_resource.Bucket(bucket)
        if bool(list(s3_bucket.objects.filter(Prefix=s3_key))):
            print("object exists, skipping")
            continue

        buf = io.BytesIO()
        asset_dir = f"{asset_root_dir}/asset.{Path(s3_key).with_suffix('')}"
        os.chdir(asset_dir)
        files = get_all_file_paths(directory=".")
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                zf.write(os.path.join(file))
        buf.seek(0)
        s3_client.upload_fileobj(Fileobj=buf, Bucket=bucket, Key=s3_key)


def find_assets(template, account_id, region):
    assets = {}
    for name, resource in template["Resources"].items():
        bucket = None
        S3Key = None

        if resource["Properties"].get("Code"):
            bucket = resource["Properties"]["Code"]["S3Bucket"]
            S3Key = resource["Properties"]["Code"]["S3Key"]
        elif resource["Properties"].get("Content"):
            bucket = resource["Properties"]["Content"]["S3Bucket"]
            S3Key = resource["Properties"]["Content"]["S3Key"]
        if S3Key and bucket:
            assets[S3Key] = bucket["Fn::Sub"].replace("${AWS::AccountId}", account_id).replace("${AWS::Region}", region)

        return assets

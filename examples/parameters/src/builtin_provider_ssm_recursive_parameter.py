from typing import Any

import boto3
import requests

from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.typing import LambdaContext

# assuming role from another account to get parameter there
# see: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
sts_client = boto3.client("sts")
assumed_role_object = sts_client.assume_role(
    RoleArn="arn:aws:iam::account-of-role-to-assume:role/name-of-role", RoleSessionName="RoleAssume1"
)
credentials = assumed_role_object["Credentials"]

# using temporary credentials in your SSMProvider provider
# see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#module-boto3.session
boto3_session = boto3.session.Session(
    region_name="us-east-1",
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"],
)
ssm_provider = parameters.SSMProvider(boto3_session=boto3_session)


def lambda_handler(event: dict, context: LambdaContext):
    try:
        # Retrieve multiple parameters from a path prefix
        all_parameters: Any = ssm_provider.get_multiple("/lambda-powertools/")
        endpoint_comments = "https://jsonplaceholder.typicode.com/noexists/"

        for parameter, value in all_parameters.items():

            if parameter == "endpoint_comments":
                endpoint_comments = value

        # the value of parameter is https://jsonplaceholder.typicode.com/comments/
        comments: requests.Response = requests.get(endpoint_comments)

        return {"comments": comments.json()[:10]}
    except parameters.exceptions.GetParameterError as error:
        return {"comments": None, "message": str(error), "statusCode": 400}

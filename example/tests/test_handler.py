import json
import os

from dataclasses import dataclass

import pytest


@pytest.fixture()
def env_vars(monkeypatch):
    monkeypatch.setenv("POWERTOOLS_METRICS_NAMESPACE", "example_namespace")
    monkeypatch.setenv("POWERTOOLS_SERVICE_NAME", "example_service")
    monkeypatch.setenv("POWERTOOLS_TRACE_DISABLED", "1")

@pytest.fixture()
def lambda_handler(env_vars):
    from hello_world import app
    return app.lambda_handler

@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "body": '{ "test": "body"}',
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


@dataclass
class Context:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = "arn:aws:lambda:eu-west-1:298026489:function:test"
    aws_request_id: str = "5b441b59-a550-11c8-6564-f1c833cf438c"


def test_lambda_handler(lambda_handler, apigw_event, mocker, capsys):
    ret = lambda_handler(apigw_event, Context())
    data = json.loads(ret["body"])

    output = capsys.readouterr()
    output = output.out.split("\n")
    stdout_one_string = "\t".join(output)

    assert ret["statusCode"] == 200
    assert data["message"] == "hello world"
    assert "location" in data
    assert "message" in ret["body"]
    assert "async_http" in data

    # assess custom metric was flushed in stdout/logs
    assert "SuccessfulLocations" in stdout_one_string
    assert "ColdStart" in stdout_one_string
    assert "UniqueMetricDimension" in stdout_one_string

    # assess our custom middleware ran
    assert "Logging response after Handler is called" in stdout_one_string
    assert "Logging event before Handler is called" in stdout_one_string

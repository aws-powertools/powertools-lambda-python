import json

from src.users import main  # follows namespace package from root


def test_lambda_handler(apigw_event, lambda_context):
    ret = main.lambda_handler(apigw_event, lambda_context)
    expected = json.dumps({"message": "hello universe"}, separators=(",", ":"))

    assert ret["statusCode"] == 200
    assert ret["body"] == expected

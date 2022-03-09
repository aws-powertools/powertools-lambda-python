import json


def hello_name(name):
    return {"statusCode": 200, "body": json.dumps({"message": f"hello {name}!"})}


def lambda_handler(event, context):
    name = event["pathParameters"]["name"]
    return hello_name(name)

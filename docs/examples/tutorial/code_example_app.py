import json


def hello():
    return {"statusCode": 200, "body": json.dumps({"message": "hello unknown!"})}


def lambda_handler(event, context):
    return hello()

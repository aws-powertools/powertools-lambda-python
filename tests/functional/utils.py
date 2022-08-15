import base64
import json

from aws_lambda_powertools.shared.json_encoder import Encoder


def str_to_b64(data: str) -> str:
    return base64.b64encode(data.encode()).decode("utf-8")


def b64_to_str(data: str) -> str:
    return base64.b64decode(data.encode()).decode("utf-8")


def json_serialize(data):
    return json.dumps(data, sort_keys=True, cls=Encoder)

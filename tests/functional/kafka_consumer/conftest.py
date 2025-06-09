import base64
import json
from dataclasses import dataclass

import pytest


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


@pytest.fixture
def lambda_context():
    return LambdaContext()


@pytest.fixture
def json_encoded_data():
    data = {"name": "John Doe", "age": 30}
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


@pytest.fixture
def kafka_event_with_json_data(json_encoded_data):
    return {
        "eventSource": "aws:kafka",
        "eventSourceArn": "arn:aws:kafka:us-east-1:123456789012:cluster/my-cluster/abcdefg",
        "records": {
            "my-topic-1": [
                {
                    "topic": "my-topic-1",
                    "partition": 0,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": json_encoded_data,
                    "headers": [{"headerKey": [104, 101, 97, 100, 101, 114, 86, 97, 108, 117, 101]}],
                },
            ],
        },
    }


@dataclass
class UserValueDataClass:
    name: str
    age: int


@pytest.fixture
def user_value_dataclass():
    return UserValueDataClass


@dataclass
class UserKeyClass:
    user_id: str


@pytest.fixture
def user_key_dataclass():
    return UserKeyClass


class UserValueDict:
    def __init__(self, name=None, age=None):
        self.name = name
        self.age = age

    def to_dict(self):
        return {"name": self.name, "age": self.age}


@pytest.fixture
def user_value_dict():
    return UserValueDict()


class UserKeyDict:
    def __init__(self, user_id=None):
        self.user_id = user_id

    def to_dict(self):
        return {"user_id": self.user_id}


@pytest.fixture
def user_key_dict():
    return UserKeyDict

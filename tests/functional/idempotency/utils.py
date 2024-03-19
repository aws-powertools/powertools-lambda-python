from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from botocore import stub
from pytest import FixtureRequest

from tests.functional.utils import json_serialize


def hash_idempotency_key(data: Any):
    """Serialize data to JSON, encode, and hash it for idempotency key"""
    return hashlib.md5(json_serialize(data).encode()).hexdigest()


def build_idempotency_put_item_stub(
    data: Dict,
    function_name: str = "test-func",
    function_qualified_name: str = "test_idempotent_lambda_first_execution_event_mutation.<locals>",
    module_name: str = "functional.idempotency.test_idempotency",
    handler_name: str = "lambda_handler",
) -> Dict:
    idempotency_key_hash = (
        f"{function_name}.{module_name}.{function_qualified_name}.{handler_name}#{hash_idempotency_key(data)}"
    )
    return {
        "ConditionExpression": (
            "attribute_not_exists(#id) OR #expiry < :now OR "
            "(#status = :inprogress AND attribute_exists(#in_progress_expiry) AND #in_progress_expiry < :now_in_millis)"
        ),
        "ReturnValuesOnConditionCheckFailure": "ALL_OLD",
        "ExpressionAttributeNames": {
            "#id": "id",
            "#expiry": "expiration",
            "#status": "status",
            "#in_progress_expiry": "in_progress_expiration",
        },
        "ExpressionAttributeValues": {
            ":now": {"N": stub.ANY},
            ":now_in_millis": {"N": stub.ANY},
            ":inprogress": {"S": "INPROGRESS"},
        },
        "Item": {
            "expiration": {"N": stub.ANY},
            "id": {"S": idempotency_key_hash},
            "status": {"S": "INPROGRESS"},
            "in_progress_expiration": {"N": stub.ANY},
        },
        "TableName": "TEST_TABLE",
    }


def build_idempotency_update_item_stub(
    data: Dict,
    handler_response: Dict,
    function_name: str = "test-func",
    function_qualified_name: str = "test_idempotent_lambda_first_execution_event_mutation.<locals>",
    module_name: str = "functional.idempotency.test_idempotency",
    handler_name: str = "lambda_handler",
) -> Dict:
    idempotency_key_hash = (
        f"{function_name}.{module_name}.{function_qualified_name}.{handler_name}#{hash_idempotency_key(data)}"
    )
    serialized_lambda_response = json_serialize(handler_response)
    return {
        "ExpressionAttributeNames": {
            "#expiry": "expiration",
            "#response_data": "data",
            "#status": "status",
        },
        "ExpressionAttributeValues": {
            ":expiry": {"N": stub.ANY},
            ":response_data": {"S": serialized_lambda_response},
            ":status": {"S": "COMPLETED"},
        },
        "Key": {"id": {"S": idempotency_key_hash}},
        "TableName": "TEST_TABLE",
        "UpdateExpression": "SET #response_data = :response_data, #expiry = :expiry, #status = :status",
    }


def build_idempotency_key_id(data: Dict, request: FixtureRequest):
    return f"test-func.{request.function.__module__}.{request.function.__qualname__}.<locals>.lambda_handler#{hash_idempotency_key(data)}"  # noqa: E501


def build_idempotency_put_item_response_stub(
    data: Dict,
    expiration: int,
    status: str,
    request: FixtureRequest,
    validation_data: Any | None,
):
    response = {
        "Item": {
            "id": {"S": build_idempotency_key_id(data, request)},
            "expiration": {"N": expiration},
            "data": {"S": json.dumps(data)},
            "status": {"S": status},
            "validation": {"S": hash_idempotency_key(validation_data)},
        },
    }

    if validation_data is not None:
        response["Item"]["validation"] = {"S": hash_idempotency_key(validation_data)}

    return response

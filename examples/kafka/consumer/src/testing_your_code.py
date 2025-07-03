import base64
import json

from lambda_handler_test import lambda_handler


def test_process_json_message():
    """Test processing a simple JSON message"""
    # Create a test Kafka event with JSON data
    test_event = {
        "eventSource": "aws:kafka",
        "records": {
            "orders-topic": [
                {
                    "topic": "orders-topic",
                    "partition": 0,
                    "offset": 15,
                    "timestamp": 1545084650987,
                    "timestampType": "CREATE_TIME",
                    "key": None,
                    "value": base64.b64encode(json.dumps({"order_id": "12345", "amount": 99.95}).encode()).decode(),
                },
            ],
        },
    }

    # Invoke the Lambda handler
    response = lambda_handler(test_event, {})

    # Verify the response
    assert response["statusCode"] == 200
    assert response.get("processed") == 1


def test_process_multiple_records():
    """Test processing multiple records in a batch"""
    # Create a test event with multiple records
    test_event = {
        "eventSource": "aws:kafka",
        "records": {
            "customers-topic": [
                {
                    "topic": "customers-topic",
                    "partition": 0,
                    "offset": 10,
                    "value": base64.b64encode(json.dumps({"customer_id": "A1", "name": "Alice"}).encode()).decode(),
                },
                {
                    "topic": "customers-topic",
                    "partition": 0,
                    "offset": 11,
                    "value": base64.b64encode(json.dumps({"customer_id": "B2", "name": "Bob"}).encode()).decode(),
                },
            ],
        },
    }

    # Invoke the Lambda handler
    response = lambda_handler(test_event, {})

    # Verify the response
    assert response["statusCode"] == 200
    assert response.get("processed") == 2

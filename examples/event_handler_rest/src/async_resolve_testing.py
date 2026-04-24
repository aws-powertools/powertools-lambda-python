import asyncio
import json


def test_async_handler():
    from async_resolve_getting_started import app  # (1)!

    event = {
        "httpMethod": "GET",
        "path": "/todos/1",
        "headers": {},
        "queryStringParameters": None,
        "pathParameters": {"todo_id": "1"},
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {"stage": "dev", "requestId": "test-id", "http": {"method": "GET", "path": "/todos/1"}},
        "rawPath": "/todos/1",
        "rawQueryString": "",
        "routeKey": "GET /todos/{todo_id}",
        "version": "2.0",
    }

    response = asyncio.run(app.resolve_async(event, {}))  # (2)!

    assert response["statusCode"] == 200  # (3)!
    assert json.loads(response["body"]) == {"todo_id": "1", "completed": False}

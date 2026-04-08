from unittest.mock import MagicMock

from dependency_injection import app, get_dynamodb_table


def test_list_orders():
    # Create a mock table
    mock_table = MagicMock()
    mock_table.scan.return_value = {"Items": [{"id": "order-1"}]}

    # Override the dependency with a lambda that returns the mock
    app.dependency_overrides[get_dynamodb_table] = lambda: mock_table

    result = app(
        {
            "requestContext": {"http": {"method": "GET", "path": "/orders"}, "stage": "$default"},
            "rawPath": "/orders",
            "headers": {},
        },
        {},
    )

    assert result["statusCode"] == 200

    # Clean up overrides after testing
    app.dependency_overrides.clear()

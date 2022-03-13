import app
import boto3


def test_idempotent_lambda():
    # Create our own Table resource using the endpoint for our DynamoDB Local instance
    resource = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
    table = resource.Table(app.persistence_layer.table_name)
    app.persistence_layer.table = table

    result = app.handler({"testkey": "testvalue"}, {})
    assert result["payment_id"] == 12345

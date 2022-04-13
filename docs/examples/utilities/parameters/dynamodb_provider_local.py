from aws_lambda_powertools.utilities import parameters

dynamodb_provider = parameters.DynamoDBProvider(
    table_name="my-table",
    endpoint_url="http://localhost:8000",
)

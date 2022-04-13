from aws_lambda_powertools.utilities import parameters

dynamodb_provider = parameters.DynamoDBProvider(table_name="my-table")


def handler(event, context):
    # Retrieve multiple values by performing a Query on the DynamoDB table
    # This returns a dict with the sort key attribute as dict key.
    parameters = dynamodb_provider.get_multiple("my-hash-key")
    for k, v in parameters.items():
        # k: param-a
        # v: "my-value-a"
        print(f"{k}: {v}")

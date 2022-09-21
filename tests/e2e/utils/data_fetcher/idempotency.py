import boto3
from retry import retry


class DynamoDB:
    def __init__(
        self,
        function_name: str,
        table_name: str,
    ):
        """Fetch and expose Powertools Idempotency key from DynamoDB

        Parameters
        ----------
        function_name : str
            Name of Lambda function to fetch dynamodb record
        table_name : str
            Name of DynamoDB table
        """
        self.function_name = function_name
        self.table_name = table_name
        self.ddb_client = boto3.resource("dynamodb")

    def get_records(self) -> int:

        table = self.ddb_client.Table(self.table_name)
        ret = table.scan(
            FilterExpression="contains (id, :functionName)",
            ExpressionAttributeValues={":functionName": f"{self.function_name}#"},
        )

        if not ret["Items"]:
            raise ValueError("Empty response from DynamoDB Repeating...")

        return ret["Count"]


@retry(ValueError, delay=2, jitter=1.5, tries=10)
def get_ddb_idempotency_record(
    function_name: str,
    table_name: str,
) -> DynamoDB:
    """_summary_

    Parameters
    ----------
    function_name : str
        Name of Lambda function to fetch dynamodb record
    table_name : str
            Name of DynamoDB table

    Returns
    -------
    DynamoDB
        DynamoDB instance with dynamodb record
    """
    return DynamoDB(function_name=function_name, table_name=table_name)

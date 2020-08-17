"""
Amazon DynamoDB parameter retrieval and caching utility
"""


from typing import Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key

from .base import BaseProvider


class DynamoDBProvider(BaseProvider):
    """
    Amazon DynamoDB Parameter Provider
    """

    table = None
    key_attr = None
    value_attr = None

    def __init__(
        self, table_name: str, key_attr: str = "id", value_attr: str = "value", region: Optional[str] = None,
    ):
        """
        Initialize the DynamoDB client
        """

        client_kwargs = {}
        if region:
            client_kwargs["region_name"] = region
        self.table = boto3.resource("dynamodb", **client_kwargs).Table(table_name)

        self.key_attr = key_attr
        self.value_attr = value_attr

        super().__init__()

    def _get(self, name: str, **kwargs) -> str:
        """
        Retrieve a parameter value from Amazon DynamoDB
        """

        return self.table.get_item(Key={self.key_attr: name})["Item"][self.value_attr]

    def _get_multiple(self, path: str, **kwargs) -> Dict[str, str]:
        """
        Retrieve multiple parameter values from Amazon DynamoDB

        Parameters
        ----------
        path: str
            Path to retrieve the parameters
        sort_attr: str
            Name of the DynamoDB table sort key (defaults to 'sk')
        """

        sort_attr = kwargs.get("sort_attr", "sk")

        response = self.table.query(KeyConditionExpression=Key(self.key_attr).eq(path))
        items = response.get("Items", [])

        # Keep querying while there are more items matching the partition key
        while "LastEvaluatedKey" in response:
            response = self.table.query(
                KeyConditionExpression=Key(self.key_attr).eq(path), ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        retval = {}
        for item in items:
            retval[item[sort_attr]] = item[self.value_attr]

        return retval

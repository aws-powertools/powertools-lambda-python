import datetime
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config

from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import DataRecord

logger = logging.getLogger(__name__)


class DynamoDBPersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        table_name: str,
        key_attr: str = "id",
        expiry_attr: str = "expiration",
        status_attr: str = "status",
        data_attr: str = "data",
        validation_key_attr: str = "validation",
        boto_config: Optional[Config] = None,
        boto3_session: Optional[boto3.session.Session] = None,
    ):
        """
        Initialize the DynamoDB client

        Parameters
        ----------
        table_name: str
            Name of the table to use for storing execution records
        key_attr: str, optional
            DynamoDB attribute name for key, by default "id"
        expiry_attr: str, optional
            DynamoDB attribute name for expiry timestamp, by default "expiration"
        status_attr: str, optional
            DynamoDB attribute name for status, by default "status"
        data_attr: str, optional
            DynamoDB attribute name for response data, by default "data"
        boto_config: botocore.config.Config, optional
            Botocore configuration to pass during client initialization
        boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication

        Examples
        --------
        **Create a DynamoDB persistence layer with custom settings**

            >>> from aws_lambda_powertools.utilities.idempotency import (
            >>>    idempotent, DynamoDBPersistenceLayer
            >>> )
            >>>
            >>> persistence_store = DynamoDBPersistenceLayer(table_name="idempotency_store")
            >>>
            >>> @idempotent(persistence_store=persistence_store)
            >>> def handler(event, context):
            >>>     return {"StatusCode": 200}
        """

        boto_config = boto_config or Config()
        session = boto3_session or boto3.session.Session()
        self._ddb_resource = session.resource("dynamodb", config=boto_config)
        self.table_name = table_name
        self.table = self._ddb_resource.Table(self.table_name)
        self.key_attr = key_attr
        self.expiry_attr = expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr
        super(DynamoDBPersistenceLayer, self).__init__()

    def _item_to_data_record(self, item: Dict[str, Any]) -> DataRecord:
        """
        Translate raw item records from DynamoDB to DataRecord

        Parameters
        ----------
        item: Dict[str, Union[str, int]]
            Item format from dynamodb response

        Returns
        -------
        DataRecord
            representation of item

        """
        return DataRecord(
            idempotency_key=item[self.key_attr],
            status=item[self.status_attr],
            expiry_timestamp=item[self.expiry_attr],
            response_data=item.get(self.data_attr),
            payload_hash=item.get(self.validation_key_attr),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        response = self.table.get_item(Key={self.key_attr: idempotency_key}, ConsistentRead=True)

        try:
            item = response["Item"]
        except KeyError:
            raise IdempotencyItemNotFoundError
        return self._item_to_data_record(item)

    def _put_record(self, data_record: DataRecord) -> None:
        item = {
            self.key_attr: data_record.idempotency_key,
            self.expiry_attr: data_record.expiry_timestamp,
            self.status_attr: data_record.status,
        }

        if self.payload_validation_enabled:
            item[self.validation_key_attr] = data_record.payload_hash

        now = datetime.datetime.now()
        try:
            logger.debug(f"Putting record for idempotency key: {data_record.idempotency_key}")
            self.table.put_item(
                Item=item,
                ConditionExpression=f"attribute_not_exists({self.key_attr}) OR {self.expiry_attr} < :now",
                ExpressionAttributeValues={":now": int(now.timestamp())},
            )
        except self._ddb_resource.meta.client.exceptions.ConditionalCheckFailedException:
            logger.debug(f"Failed to put record for already existing idempotency key: {data_record.idempotency_key}")
            raise IdempotencyItemAlreadyExistsError

    def _update_record(self, data_record: DataRecord):
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        update_expression = "SET #response_data = :response_data, #expiry = :expiry, #status = :status"
        expression_attr_values = {
            ":expiry": data_record.expiry_timestamp,
            ":response_data": data_record.response_data,
            ":status": data_record.status,
        }
        expression_attr_names = {
            "#response_data": self.data_attr,
            "#expiry": self.expiry_attr,
            "#status": self.status_attr,
        }

        if self.payload_validation_enabled:
            update_expression += ", #validation_key = :validation_key"
            expression_attr_values[":validation_key"] = data_record.payload_hash
            expression_attr_names["#validation_key"] = self.validation_key_attr

        kwargs = {
            "Key": {self.key_attr: data_record.idempotency_key},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attr_values,
            "ExpressionAttributeNames": expression_attr_names,
        }

        self.table.update_item(**kwargs)

    def _delete_record(self, data_record: DataRecord) -> None:
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")
        self.table.delete_item(Key={self.key_attr: data_record.idempotency_key})

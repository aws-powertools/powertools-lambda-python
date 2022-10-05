import datetime
import logging
import os
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import (
    STATUS_CONSTANTS,
    DataRecord,
)

logger = logging.getLogger(__name__)


class DynamoDBPersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        table_name: str,
        key_attr: str = "id",
        static_pk_value: Optional[str] = None,
        sort_key_attr: Optional[str] = None,
        expiry_attr: str = "expiration",
        in_progress_expiry_attr: str = "in_progress_expiration",
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
            DynamoDB attribute name for partition key, by default "id"
        static_pk_value: str, optional
            DynamoDB attribute value for partition key, by default "idempotency#<function-name>".
            This will be used if the sort_key_attr is set.
        sort_key_attr: str, optional
            DynamoDB attribute name for the sort key
        expiry_attr: str, optional
            DynamoDB attribute name for expiry timestamp, by default "expiration"
        in_progress_expiry_attr: str, optional
            DynamoDB attribute name for in-progress expiry timestamp, by default "in_progress_expiration"
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

        self._boto_config = boto_config or Config()
        self._boto3_session = boto3_session or boto3.session.Session()
        if sort_key_attr == key_attr:
            raise ValueError(f"key_attr [{key_attr}] and sort_key_attr [{sort_key_attr}] cannot be the same!")

        if static_pk_value is None:
            static_pk_value = f"idempotency#{os.getenv(constants.LAMBDA_FUNCTION_NAME_ENV, '')}"

        self._table = None
        self.table_name = table_name
        self.key_attr = key_attr
        self.static_pk_value = static_pk_value
        self.sort_key_attr = sort_key_attr
        self.expiry_attr = expiry_attr
        self.in_progress_expiry_attr = in_progress_expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr
        super(DynamoDBPersistenceLayer, self).__init__()

    @property
    def table(self):
        """
        Caching property to store boto3 dynamodb Table resource

        """
        if self._table:
            return self._table
        ddb_resource = self._boto3_session.resource("dynamodb", config=self._boto_config)
        self._table = ddb_resource.Table(self.table_name)
        return self._table

    @table.setter
    def table(self, table):
        """
        Allow table instance variable to be set directly, primarily for use in tests
        """
        self._table = table

    def _get_key(self, idempotency_key: str) -> dict:
        if self.sort_key_attr:
            return {self.key_attr: self.static_pk_value, self.sort_key_attr: idempotency_key}
        return {self.key_attr: idempotency_key}

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
            in_progress_expiry_timestamp=item.get(self.in_progress_expiry_attr),
            response_data=item.get(self.data_attr),
            payload_hash=item.get(self.validation_key_attr),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        response = self.table.get_item(Key=self._get_key(idempotency_key), ConsistentRead=True)

        try:
            item = response["Item"]
        except KeyError:
            raise IdempotencyItemNotFoundError
        return self._item_to_data_record(item)

    def _put_record(self, data_record: DataRecord) -> None:
        item = {
            **self._get_key(data_record.idempotency_key),
            self.expiry_attr: data_record.expiry_timestamp,
            self.status_attr: data_record.status,
        }

        if data_record.in_progress_expiry_timestamp is not None:
            item[self.in_progress_expiry_attr] = data_record.in_progress_expiry_timestamp

        if self.payload_validation_enabled:
            item[self.validation_key_attr] = data_record.payload_hash

        now = datetime.datetime.now()
        try:
            logger.debug(f"Putting record for idempotency key: {data_record.idempotency_key}")

            # |     LOCKED     |         RETRY if status = "INPROGRESS"                |     RETRY
            # |----------------|-------------------------------------------------------|-------------> .... (time)
            # |             Lambda                                              Idempotency Record
            # |             Timeout                                                 Timeout
            # |       (in_progress_expiry)                                          (expiry)

            # Conditions to successfully save a record:

            # The idempotency key does not exist:
            #    - first time that this invocation key is used
            #    - previous invocation with the same key was deleted due to TTL
            idempotency_key_not_exist = "attribute_not_exists(#id)"

            # The idempotency record exists but it's expired:
            idempotency_expiry_expired = "#expiry < :now"

            # The status of the record is "INPROGRESS", there is an in-progress expiry timestamp, but it's expired
            inprogress_expiry_expired = " AND ".join(
                [
                    "#status = :inprogress",
                    "attribute_exists(#in_progress_expiry)",
                    "#in_progress_expiry < :now_in_millis",
                ]
            )

            condition_expression = (
                f"{idempotency_key_not_exist} OR {idempotency_expiry_expired} OR ({inprogress_expiry_expired})"
            )

            self.table.put_item(
                Item=item,
                ConditionExpression=condition_expression,
                ExpressionAttributeNames={
                    "#id": self.key_attr,
                    "#expiry": self.expiry_attr,
                    "#in_progress_expiry": self.in_progress_expiry_attr,
                    "#status": self.status_attr,
                },
                ExpressionAttributeValues={
                    ":now": int(now.timestamp()),
                    ":now_in_millis": int(now.timestamp() * 1000),
                    ":inprogress": STATUS_CONSTANTS["INPROGRESS"],
                },
            )
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            logger.debug(f"Failed to put record for already existing idempotency key: {data_record.idempotency_key}")
            raise IdempotencyItemAlreadyExistsError

    def _update_record(self, data_record: DataRecord):
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        update_expression = "SET #response_data = :response_data, #expiry = :expiry, " "#status = :status"
        expression_attr_values = {
            ":expiry": data_record.expiry_timestamp,
            ":response_data": data_record.response_data,
            ":status": data_record.status,
        }
        expression_attr_names = {
            "#expiry": self.expiry_attr,
            "#response_data": self.data_attr,
            "#status": self.status_attr,
        }

        if self.payload_validation_enabled:
            update_expression += ", #validation_key = :validation_key"
            expression_attr_values[":validation_key"] = data_record.payload_hash
            expression_attr_names["#validation_key"] = self.validation_key_attr

        kwargs = {
            "Key": self._get_key(data_record.idempotency_key),
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attr_values,
            "ExpressionAttributeNames": expression_attr_names,
        }

        self.table.update_item(**kwargs)

    def _delete_record(self, data_record: DataRecord) -> None:
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")
        self.table.delete_item(Key=self._get_key(data_record.idempotency_key))

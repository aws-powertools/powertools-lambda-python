"""
Persistence layers supporting idempotency
"""

import datetime
import hashlib
import json
import pickle
from abc import ABC, abstractmethod
from base64 import b64decode, b64encode
from typing import Any, Dict, Iterable, Optional, Union

import boto3
import jmespath
from botocore.config import Config

from .exceptions import InvalidStatusError, ItemAlreadyExistsError, ItemNotFoundError

STATUS_CONSTANTS = {
    "NOTEXISTING": "DOESNOTEXIST",
    "INPROGRESS": "INPROGRESS",
    "COMPLETED": "COMPLETED",
    "EXPIRED": "EXPIRED",
    "ERROR": "ERROR",
}


class DataRecord:
    """
    Data Class for idempotency records.
    """

    def __init__(
        self, idempotency_key, status: str = None, expiry_timestamp: int = None, response_data: str = None
    ) -> None:
        """

        Parameters
        ----------
        idempotency_key: str
            hashed representation of the idempotent data
        status: str, optional
            status of the idempotent record
        expiry_timestamp: int, optional
            time before the record should expire, in milliseconds
        response_data: str, optional
            response data from previous executions using the record
        """
        self.idempotency_key = idempotency_key
        self.expiry_timestamp = expiry_timestamp
        self._status = status
        self.response_data = response_data

    @property
    def is_expired(self) -> bool:
        """
        Check if data record is expired

        Returns
        -------
        bool
            Whether the record is currently expired or not
        """
        if self.expiry_timestamp:
            if int(datetime.datetime.now().timestamp()) > self.expiry_timestamp:
                return True
        return False

    @property
    def status(self) -> str:
        """
        Get status of data record

        Returns
        -------
        str
        """
        if self.is_expired:
            return STATUS_CONSTANTS["EXPIRED"]

        if self._status in STATUS_CONSTANTS.values():
            return self._status
        else:
            raise InvalidStatusError(self._status)

    def response_json_as_dict(self) -> dict:
        """
        Get response data deserialized to python dict

        Returns
        -------
        dict
            previous response data deserialized
        """
        return json.loads(self.response_data)

    def raise_stored_exception(self):
        """
        Raises
        ------
        Exception
            Decoded and unpickled Exception from persistent store
        """

        decoded_exception = pickle.loads(b64decode(self.response_data.encode()))
        raise decoded_exception


class BasePersistenceLayer(ABC):
    """
    Abstract Base Class for Idempotency persistence layer.
    """

    def __init__(
        self, event_key: str, expires_after: int = 3600, non_retryable_errors: Optional[Iterable[Exception]] = None
    ) -> None:
        """
        Initialize the base persistence layer

        Parameters
        ----------
        event_key: str
            A jmespath expression to extract the idempotency key from the event record
        expires_after: int
            The number of milliseconds to wait before a record is expired
        non_retryable_errors: Iterable, optional
            An interable of exception classes which should not be retried after being raised, by default []
        """
        self.event_key = event_key
        self.event_key_jmespath = jmespath.compile(event_key)
        self.expires_after = expires_after
        self.non_retryable_errors = non_retryable_errors or []

    def get_hashed_idempotency_key(self, lambda_event: Dict[str, Any]) -> str:
        """
        Extract data from lambda event using event key jmespath, and return a hashed representation

        Parameters
        ----------
        lambda_event: Dict[str, Any]
            Lambda event

        Returns
        -------
        str
            md5 hash of the data extracted by the jmespath expression

        """
        data = self.event_key_jmespath.search(lambda_event)
        hashed_data = hashlib.md5(json.dumps(data).encode())
        return hashed_data.hexdigest()

    def _get_expiry_timestamp(self) -> int:
        """

        Returns
        -------
        int
            unix timestamp of expiry date for idempotency record

        """
        now = datetime.datetime.now()
        period = datetime.timedelta(seconds=self.expires_after)
        return int((now + period).timestamp())

    def save_success(self, event: Dict[str, Any], result: dict) -> None:
        """
        Save record of function's execution completing succesfully

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        result: dict
            The response from lambda handler
        """
        response_data = json.dumps(result)

        data_record = DataRecord(
            idempotency_key=self.get_hashed_idempotency_key(event),
            status=STATUS_CONSTANTS["COMPLETED"],
            expiry_timestamp=self._get_expiry_timestamp(),
            response_data=response_data,
        )
        self._update_record(data_record=data_record)

    def save_inprogress(self, event: Dict[str, Any]) -> None:
        """
        Save record of function's execution being in progress

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        """
        data_record = DataRecord(
            idempotency_key=self.get_hashed_idempotency_key(event),
            status=STATUS_CONSTANTS["INPROGRESS"],
            expiry_timestamp=self._get_expiry_timestamp(),
        )
        self._put_record(data_record)

    def save_error(self, event: Dict[str, Any], exception: Exception):
        """
        Save record of lambda handler raising an exception

        Parameters
        ----------
        event: Dict[str, Any]
            Lambda event
        exception
            The exception raised by the lambda handler
        """
        data_record = DataRecord(
            idempotency_key=self.get_hashed_idempotency_key(event),
            status=STATUS_CONSTANTS["ERROR"],
            expiry_timestamp=self._get_expiry_timestamp(),
        )

        # Only write a record of the error to the persistent store if it is not a subclass of any of the non retryable
        # error classes
        if not self._is_retryable(exception):
            data_record.response_data = b64encode(pickle.dumps(exception)).decode()
            self._update_record(data_record)
        else:
            # If the error is retryable, delete the in progress record from the store
            self._delete_record(data_record)

    def _is_retryable(self, exception: Exception):
        """
        Check whether the exception is retryable or not

        Parameters
        ----------
        exception: Exception
            exception instance raised by lambda handler

        Returns
        -------
        bool
            Whether exception should be retried in the future or not
        """
        return not any((issubclass(exception.__class__, nr) for nr in self.non_retryable_errors))

    def get_record(self, lambda_event) -> DataRecord:
        """
        Calculate idempotency key for lambda_event, then retrieve item from persistence store using idempotency key
        and return it as a DataRecord instance.and return it as a DataRecord instance.

        Parameters
        ----------
        lambda_event: Dict[str, Any]

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        ItemNotFound
            Exception raised if no record exists in persistence store with the idempotency key
        """

        idempotency_key = self.get_hashed_idempotency_key(lambda_event)

        return self._get_record(idempotency_key)

    @abstractmethod
    def _get_record(self, idempotency_key) -> DataRecord:
        """
        Retrieve item from persistence store using idempotency key and return it as a DataRecord instance.

        Parameters
        ----------
        idempotency_key

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        ItemNotFound
            Exception raised if no record exists in persistence store with the idempotency key
        """
        raise NotImplementedError

    @abstractmethod
    def _put_record(self, data_record: DataRecord) -> None:
        """
        Add a DataRecord to persistence store if it does not already exist with that key. Raise ItemAlreadyExists
        if an entry already exists.

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _update_record(self, data_record: DataRecord) -> None:
        """
        Update item in persistence store

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _delete_record(self, data_record: DataRecord) -> None:
        """
        Remove item from persistence store
        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError


class DynamoDBPersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        table_name: str,  # Can we use the lambda function name?
        key_attr: Optional[str] = "id",
        expiry_attr: Optional[str] = "expiration",
        status_attr: Optional[str] = "status",
        data_attr: Optional[str] = "data",
        boto_config: Optional[Config] = None,
        create_table_if_not_existing: Optional[bool] = False,
        *args,
        **kwargs,
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
        create_table_if_not_existing: bool, optional
            Whether to create the dynamodb table if it doesn't already exist, by default False
        args
        kwargs

        Examples
        --------
        **Create a DynamoDB persistence layer with custom settings**
            >>> from aws_lambda_powertools.utilities.idempotency import idempotent, DynamoDBPersistenceLayer
            >>>
            >>> persistence_store = DynamoDBPersistenceLayer(event_key="body", table_name="idempotency_store")
            >>>
            >>> @idempotent(persistence=persistence_store)
            >>> def handler(event, context):
            >>>     return {"StatusCode": 200}
        """

        boto_config = boto_config or Config()
        self._ddb_resource = boto3.resource("dynamodb", config=boto_config)
        self.table_name = table_name
        self.table = self._ddb_resource.Table(self.table_name)
        self.key_attr = key_attr
        self.expiry_attr = expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.create_table_if_not_existing = create_table_if_not_existing
        super(DynamoDBPersistenceLayer, self).__init__(*args, **kwargs)

        if self.create_table_if_not_existing:
            self._check_and_create_table()

    def _check_and_create_table(self) -> None:
        """
        Check if DynamoDB table exists already, create it if not
        """
        try:
            client = self._ddb_resource.meta.client
            table_ttl_description = client.describe_time_to_live(TableName=self.table_name)
            ttl_setting = table_ttl_description["TimeToLiveDescription"]["TimeToLiveStatus"]
            if ttl_setting == "DISABLED":
                self._set_table_ttl()

        except self._ddb_resource.meta.client.exceptions.ResourceNotFoundException:
            if self.create_table_if_not_existing:
                self._create_table()
                self._wait_for_table()
                self._set_table_ttl()

    def _create_table(self) -> None:
        """
        Create DynamoDB table
        """
        self._ddb_resource.create_table(
            TableName=self.table_name,
            KeySchema=[{"AttributeName": self.key_attr, "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": self.key_attr, "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

    def _wait_for_table(self) -> None:
        """
        Wait for table to finish being created
        """
        waiter = self._ddb_resource.meta.client.get_waiter("table_exists")
        waiter.wait(TableName=self.table_name, WaiterConfig={"Delay": 5, "MaxAttempts": 6})

    def _set_table_ttl(self) -> None:
        """
        Set TTL on table to track the expiry attribute
        """
        self._ddb_resource.meta.client.update_time_to_live(
            TableName=self.table_name, TimeToLiveSpecification={"Enabled": True, "AttributeName": self.expiry_attr}
        )

    def _item_to_data_record(self, item: Dict[str, Union[str, int]]) -> DataRecord:
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
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        try:
            response = self.table.get_item(Key={self.key_attr: idempotency_key}, ConsistentRead=True)
        except self._ddb_resource.meta.client.exceptions.ResourceNotFoundException:
            if self.create_table_if_not_existing:
                self._create_table()
                response = {}
            else:
                raise

        try:
            item = response["Item"]
        except KeyError:
            raise ItemNotFoundError
        return self._item_to_data_record(item)

    def _put_record(self, data_record: DataRecord) -> None:
        now = datetime.datetime.now()
        try:
            self.table.put_item(
                Item={
                    self.key_attr: data_record.idempotency_key,
                    "expiration": data_record.expiry_timestamp,
                    "status": STATUS_CONSTANTS["INPROGRESS"],
                },
                ConditionExpression=f"attribute_not_exists({self.key_attr}) OR expiration < :now",
                ExpressionAttributeValues={":now": int(now.timestamp())},
            )
        except self._ddb_resource.meta.client.exceptions.ConditionalCheckFailedException:
            raise ItemAlreadyExistsError

    def _update_record(self, data_record: DataRecord):

        self.table.update_item(
            Key={self.key_attr: data_record.idempotency_key},
            UpdateExpression="SET #response_data = :response_data, #expiry = :expiry, #status = :status",
            ExpressionAttributeValues={
                ":expiry": data_record.expiry_timestamp,
                ":response_data": data_record.response_data,
                ":status": data_record.status,
            },
            ExpressionAttributeNames={
                "#response_data": self.data_attr,
                "#expiry": self.expiry_attr,
                "#status": self.status_attr,
            },
        )

    def _delete_record(self, data_record: DataRecord) -> None:
        self.table.delete_item(Key={self.key_attr: data_record.idempotency_key},)

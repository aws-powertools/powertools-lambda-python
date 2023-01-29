import logging
import os
from typing import Any, Dict, Optional

import redis

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemNotFoundError,
    IdempotencyPersistenceLayerError,
    IdempotencyRedisConnectionError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.base import DataRecord

logger = logging.getLogger(__name__)


class RedisCachePersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        host: str,
        port: int = "6379",
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: int = "0",
        static_pk_value: Optional[str] = None,
        expiry_attr: str = "expiration",
        in_progress_expiry_attr: str = "in_progress_expiration",
        status_attr: str = "status",
        data_attr: str = "data",
        validation_key_attr: str = "validation",
    ):
        """
        Initialize the Redis client
        Parameters
        ----------
        host: str
            Name of the host to connect to Redis instance/cluster
        port: int
            Number of the port to connect to Redis instance/cluster
        username: str
            Name of the username to connect to Redis instance/cluster in case of using ACL
            See: https://redis.io/docs/management/security/acl/
        password: str
            Password to connect to Redis instance/cluster
        db_index: int
            Index of Redis database
            See: https://redis.io/commands/select/
        static_pk_value: str, optional
            Redis attribute value for cache key, by default "idempotency#<function-name>".
        expiry_attr: str, optional
            Redis hash attribute name for expiry timestamp, by default "expiration"
        in_progress_expiry_attr: str, optional
            Redis hash attribute name for in-progress expiry timestamp, by default "in_progress_expiration"
        status_attr: str, optional
            Redis hash attribute name for status, by default "status"
        data_attr: str, optional
            Redis hash attribute name for response data, by default "data"
        """

        self._connection = None
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index

        if static_pk_value is None:
            static_pk_value = f"idempotency#{os.getenv(constants.LAMBDA_FUNCTION_NAME_ENV, '')}"

        self.static_pk_value = static_pk_value
        self.in_progress_expiry_attr = in_progress_expiry_attr
        self.expiry_attr = expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr
        super(RedisCachePersistenceLayer, self).__init__()

    @property
    def connection(self):
        """
        Caching property to store redis connection
        """
        if self._connection:
            return self._connection

        logger.info(f"Trying to connect to Redis Host/Cluster: {self.host}")

        try:
            self._connection = redis.Redis(
                host=self.host, port=self.port, username=self.username, password=self.password, db=self.db_index
            )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis Host: {self.host}")
            raise IdempotencyRedisConnectionError("Could not to connect to Redis", exc) from exc
        return self._connection

    @connection.setter
    def connection(self, connection):
        """
        Allow redis connection variable to be set directly, primarily for use in tests
        """
        self._connection = connection

    def _get_key(self, idempotency_key: str) -> dict:
        # Need to review this after adding GETKEY logic
        if self.sort_key_attr:
            return {self.key_attr: self.static_pk_value, self.sort_key_attr: idempotency_key}
        return {self.key_attr: idempotency_key}

    def _item_to_data_record(self, item: Dict[str, Any]) -> DataRecord:
        # Need to review this after adding GETKEY logic
        return DataRecord(
            idempotency_key=item[self.key_attr],
            status=item[self.status_attr],
            expiry_timestamp=item[self.expiry_attr],
            in_progress_expiry_timestamp=item.get(self.in_progress_expiry_attr),
            response_data=item.get(self.data_attr),
            payload_hash=item.get(self.validation_key_attr),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        # See: https://redis.io/commands/hgetall/
        response = self.connection.hgetall(idempotency_key)

        try:
            item = response
        except KeyError:
            raise IdempotencyItemNotFoundError
        return self._item_to_data_record(item)

    def _put_record(self, data_record: DataRecord) -> None:

        # Redis works with hset to support hashing keys with multiple attributes
        # See: https://redis.io/commands/hset/
        item = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.in_progress_expiry_attr: data_record.in_progress_expiry_timestamp,
                self.status_attr: data_record.status,
            },
        }

        try:
            logger.debug(f"Putting record on Redis for idempotency key: {data_record.idempotency_key}")
            self.connection.hset(**item)
            # hset type must set expiration after adding the record
            # Need to review this to get ttl in seconds
            self.connection.expire(name=data_record.idempotency_key, time=60)
        except Exception as exc:
            logger.debug(f"Failed to add record idempotency key: {data_record.idempotency_key}")
            raise IdempotencyPersistenceLayerError(
                f"Failed to add record idempotency key: {data_record.idempotency_key}", exc
            ) from exc

    def _update_record(self, data_record: DataRecord) -> None:
        item = {
            "name": data_record.idempotency_key,
            "mapping": {
                self.data_attr: data_record.response_data,
                self.status_attr: data_record.status,
            },
        }
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        self.connection.hset(**item)

    def _delete_record(self, data_record: DataRecord) -> None:
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")
        # See: https://redis.io/commands/del/
        self.connection.delete(data_record.idempotency_key)

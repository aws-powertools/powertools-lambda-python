import logging
from typing import Optional

import redis

from aws_lambda_powertools.utilities.database.exceptions import RedisConnectionError

logger = logging.getLogger(__name__)


class RedisStandalone:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: Optional[int] = None,
        url: Optional[str] = None,
    ) -> None:
        """
        Initialize the Redis standalone client
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
        url: str
            Redis client object configured from the given URL
            See: https://redis.readthedocs.io/en/latest/connections.html#redis.Redis.from_url
        """

        self.url = url
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index
        self._connection = None

    def get_redis_connection(self):
        """
        Connection is cached, so returning this
        """
        if self._connection:
            return self._connection

        logger.info(f"Trying to connect to Redis Host/Cluster: {self.host}")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis: {self.host}")
                self._connection = redis.Redis.from_url(url=self.url)
            else:
                logger.debug(f"Using other parameters to connect to Redis: {self.host}")
                self._connection = redis.Redis(
                    host=self.host, port=self.port, username=self.username, password=self.password, db=self.db_index
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis Host: {self.host}")
            raise RedisConnectionError("Could not to connect to Redis Standalone", exc) from exc

        return self._connection


class RedisCluster:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        read_from_replicas: Optional[bool] = False,
        url: Optional[str] = None,
    ) -> None:
        """
        Initialize the Redis standalone client
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
            Passwod to connect to Redis instance/cluster
        db_index: int
            Index of Redis database
            See: https://redis.io/commands/select/
        url: str
            Redis client object configured from the given URL
            See: https://redis.readthedocs.io/en/latest/connections.html#redis.Redis.from_url
        """

        self.url = url
        self.host = host
        self.port = port
        self.read_from_replicas = read_from_replicas
        self._connection = None

    def get_redis_connection(self):
        """
        Connection is cached, so returning this
        """
        if self._connection:
            return self._connection

        logger.info(f"Trying to connect to Redis Cluster: {self.host}")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis Cluster: {self.host}")
                self._connection = redis.Redis.from_url(url=self.url)
            else:
                logger.debug(f"Using other parameters to connect to Redis Cluster: {self.host}")
                self._connection = redis.cluster.RedisCluster(
                    host=self.host,
                    port=self.port,
                    server_type=None,
                    read_from_replicas=self.read_from_replicas,
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis Cluster: {self.host}")
            raise RedisConnectionError("Could not to connect to Redis Cluster", exc) from exc

        return self._connection

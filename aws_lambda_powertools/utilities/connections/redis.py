import logging
from typing import Optional, Type, Union

import redis

from .base_sync import BaseConnectionSync
from .exceptions import RedisConnectionError

logger = logging.getLogger(__name__)


class RedisConnection(BaseConnectionSync):
    def __init__(
        self,
        client: Type[Union[redis.Redis, redis.RedisCluster]],
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: Optional[int] = None,
        url: Optional[str] = None,
        **extra_options,
    ) -> None:
        self.extra_options: dict = {}

        self.url = url
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_index = db_index
        self.extra_options.update(**extra_options)
        self._connection = None
        self._client = client

    def init_connection(self):
        """
        Connection is cached, so returning this
        """
        if self._connection:
            return self._connection

        logger.info(f"Trying to connect to Redis: {self.host}")

        try:
            if self.url:
                logger.debug(f"Using URL format to connect to Redis: {self.host}")
                self._connection = self._client.from_url(url=self.url)
            else:
                logger.debug(f"Using other parameters to connect to Redis: {self.host}")
                self._connection = self._client(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    db=self.db_index,
                    decode_responses=True,
                    **self.extra_options,
                )
        except redis.exceptions.ConnectionError as exc:
            logger.debug(f"Cannot connect in Redis: {self.host}")
            raise RedisConnectionError("Could not to connect to Redis", exc) from exc

        return self._connection


class RedisStandalone(RedisConnection):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: Optional[int] = None,
        url: Optional[str] = None,
        **extra_options,
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
        print(extra_options)
        super().__init__(redis.Redis, host, port, username, password, db_index, url, **extra_options)


class RedisCluster(RedisConnection):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_index: Optional[int] = None,
        url: Optional[str] = None,
        **extra_options,
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

        super().__init__(redis.cluster.RedisCluster, host, port, username, password, db_index, url, **extra_options)

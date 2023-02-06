class RedisConnectionError(Exception):
    """
    Payload does not contain an idempotent key
    """

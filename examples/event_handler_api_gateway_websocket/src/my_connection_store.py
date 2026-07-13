# Illustrative connection store. In production, back these functions with a durable store
# such as a DynamoDB table: the WebSocket resolver and the functions that push results run
# in different Lambda execution environments and cannot share process memory.

_connections: dict[str, str] = {}


def save(connection_id: str, callback_url: str) -> None:
    _connections[connection_id] = callback_url


def get_callback_url(connection_id: str) -> str:
    return _connections[connection_id]


def all_connection_ids() -> list[str]:
    return list(_connections)


def delete(connection_id: str) -> None:
    _connections.pop(connection_id, None)

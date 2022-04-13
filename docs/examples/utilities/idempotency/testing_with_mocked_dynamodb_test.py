from unittest.mock import MagicMock

import app


def test_idempotent_lambda():
    table = MagicMock()
    app.persistence_layer.table = table
    result = app.handler({"testkey": "testvalue"}, {})
    table.put_item.assert_called()
    ...

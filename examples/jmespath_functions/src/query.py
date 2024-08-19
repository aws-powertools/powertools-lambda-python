from __future__ import annotations

from typing import TYPE_CHECKING

from aws_lambda_powertools.utilities.jmespath_utils import query
from aws_lambda_powertools.utilities.typing import LambdaContext

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    payload = query(data=event, envelope="powertools_json(body)")
    customer_id = payload.get("customerId")  # now deserialized

    # also works for fetching and flattening deeply nested data
    some_data = query(data=event, envelope="deeply_nested[*].some_data[]")

    return {"customer_id": customer_id, "message": "success", "context": some_data, "statusCode": 200}

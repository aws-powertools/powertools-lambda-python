import base64
import json

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: KinesisFirehoseEvent, context: LambdaContext):
    result = []

    for record in event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_json

        processed_record = {
            "recordId": record.record_id,
            "data": base64.b64encode(json.dumps(data).encode("utf-8")),
            "result": "Ok",
        }

        result.append(processed_record)

    # return transformed records
    return {"records": result}

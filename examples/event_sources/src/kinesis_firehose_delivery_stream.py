import json

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseEvent,
    KinesisFirehoseResponceFactory,
    KinesisFirehoseResponceRecordFactory,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: KinesisFirehoseEvent, context: LambdaContext):
    result = []

    for record in event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_json

        processed_record = KinesisFirehoseResponceRecordFactory(
            record_id=record.record_id,
            result="Ok",
            data=(json.dumps(data)),
        )

        result.append(processed_record)

    # return transformed records
    return KinesisFirehoseResponceFactory(records=result)

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseEvent,
    KinesisFirehoseResponse,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: KinesisFirehoseEvent, context: LambdaContext):
    result = KinesisFirehoseResponse()

    for record in event.records:
        # if data was delivered as json; caches loaded value
        data = record.data_as_json

        ## do all kind of stuff with data
        ## generate data to return
        new_data = {"tool_used": "powertools_dataclass", "original_payload": data}

        processed_record = record.create_firehose_response_record(result="Ok")
        processed_record.data_from_json(data=new_data)

        result.add_record(processed_record)

    # return transformed records
    return result.asdict()

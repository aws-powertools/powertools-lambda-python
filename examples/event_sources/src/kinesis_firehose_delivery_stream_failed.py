from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseDataTransformationResponse,
    KinesisFirehoseEvent,
    event_source,
)
from aws_lambda_powertools.utilities.serialization import base64_from_json
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=KinesisFirehoseEvent)
def lambda_handler(event: KinesisFirehoseEvent, context: LambdaContext):
    result = KinesisFirehoseDataTransformationResponse()

    for record in event.records:
        # get original data using data_as_text property
        data = record.data_as_text

        ## do all kind of stuff with data
        ## generate data to return
        transformed_data = {"new_data": "transformed data using Powertools", "original_payload": data}

        # some process failed, send back to kinesis
        processed_record = record.build_data_transformation_response(
            data=base64_from_json(transformed_data),
            result="ProcessingFailed",
        )

        result.add_record(processed_record)

    # return transformed records
    return result.asdict()

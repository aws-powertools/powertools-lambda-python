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
        data = record.data_as_text  # (1)!

        ## generate data to return
        transformed_data = {"new_data": "transformed data using Powertools", "original_payload": data}

        processed_record = record.build_data_transformation_response(
            data=base64_from_json(transformed_data),  # (2)!
        )

        result.add_record(processed_record)

    # return transformed records
    return result.asdict()

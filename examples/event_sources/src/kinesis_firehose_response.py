import base64

from aws_lambda_powertools.utilities.data_classes import (
    KinesisFirehoseResponse,
    KinesisFirehoseResponseRecord,
)


def lambda_handler(event, context):
    result = KinesisFirehoseResponse()

    for record in event["records"]:
        print(record["recordId"])
        payload = base64.b64decode(record["data"]).decode("utf-8")
        ## do all kind of stuff with payload
        ## generate data to return
        new_data = {"tool_used": "powertools_dataclass", "original_payload": payload}

        processed_record = KinesisFirehoseResponseRecord(record_id=record["recordId"], result="Ok")
        processed_record.data_from_text(data=new_data)
        result.add_record(processed_record)

    # return transformed records
    return result.asdict()
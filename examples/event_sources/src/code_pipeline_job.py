from aws_lambda_powertools.utilities.data_classes import CodePipelineJobEvent, event_source


@event_source(data_class=CodePipelineJobEvent)
def lambda_handler(event: CodePipelineJobEvent, context):
    job_id = event.get_id

    input_bucket = event.input_bucket_name

    return {"statusCode": 200, "body": f"Processed job {job_id} from bucket {input_bucket}"}

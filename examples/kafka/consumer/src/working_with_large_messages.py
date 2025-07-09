from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

schema_config = SchemaConfig(value_schema_type="JSON")


def process_standard_message(message):
    # Simulate processing logic
    logger.info(f"Processing standard message: {message}")


def process_catalog_from_s3(bucket, key):
    # Simulate processing logic
    return {"bucket": bucket, "key": key}


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Example: Handle large product catalog updates differently
        if "large-product-update" in record.headers:
            logger.info("Detected large product catalog update")

            # Example: Extract S3 reference from message
            catalog_ref = record.value.get("s3_reference")
            logger.info(f"Processing catalog from S3: {catalog_ref}")

            # Process via S3 reference instead of direct message content
            result = process_catalog_from_s3(bucket=catalog_ref["bucket"], key=catalog_ref["key"])
            logger.info(f"Processed {result['product_count']} products from S3")
        else:
            # Regular processing for standard-sized messages
            process_standard_message(record.value)

    return {"statusCode": 200}

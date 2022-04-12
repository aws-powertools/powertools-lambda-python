from aws_lambda_powertools.utilities.batch import PartialSQSProcessor

...

processor = PartialSQSProcessor(config=config, suppress_exception=True)

with processor(records, record_handler):
    result = processor.process()

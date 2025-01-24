from aws_lambda_powertools.utilities.parser import parse
from aws_lambda_powertools.utilities.parser.models import SqsModel
from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext) -> list:
    parsed_event = parse(model=SqsModel, event=event)

    results = []
    for record in parsed_event.Records:
        results.append(
            {
                "message_id": record.messageId,
                "body": record.body,
            },
        )
    return results

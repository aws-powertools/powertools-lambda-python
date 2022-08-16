from typing import Dict, List

from aws_lambda_powertools import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()


@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext):
    annotations: List[Dict] = event.get("annotations", [])
    metadata: List[Dict] = event.get("annotations", [])

    # Maintenance: create a public method to set these explicitly
    # Maintenance: move Tracer annotations code after execution
    tracer.service = event.get("service")  # TODO: change deployment to include env var, as you can't set dynamically

    for annotation, meta in zip(annotations, metadata):
        tracer.put_annotation(**annotation)
        tracer.put_metadata(**meta)

    return "success"

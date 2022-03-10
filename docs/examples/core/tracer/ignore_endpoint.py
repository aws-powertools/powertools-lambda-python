from aws_lambda_powertools import Tracer

tracer = Tracer()
# ignore all calls to `ec2.amazon.com`
tracer.ignore_endpoint(hostname="ec2.amazon.com")
# ignore calls to `*.sensitive.com/password` and  `*.sensitive.com/credit-card`
tracer.ignore_endpoint(hostname="*.sensitive.com", urls=["/password", "/credit-card"])


def ec2_api_calls():
    return "suppress_api_responses"


@tracer.capture_lambda_handler
def handler(event, context):
    for x in long_list:
        ec2_api_calls()

from aws_lambda_powertools import Tracer

tracer = Tracer()


@tracer.capture_method
def collect_payment(charge_id):
    ret = requests.post(PAYMENT_ENDPOINT)  # logic
    tracer.put_annotation("PAYMENT_STATUS", "SUCCESS")  # custom annotation
    return ret

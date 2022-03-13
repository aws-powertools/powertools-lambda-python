from aws_lambda_powertools import Logger

logger = Logger(child=True)  # POWERTOOLS_SERVICE_NAME: "payment"


def inject_payment_id(event):
    logger.structure_logs(append=True, payment_id=event.get("payment_id"))

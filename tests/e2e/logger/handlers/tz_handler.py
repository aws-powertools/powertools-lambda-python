import os
import time

from aws_lambda_powertools import Logger


def lambda_handler(event, context):
    utc, datefmt, tz = event.get("utc", False), event.get("datefmt", None), event.get("tz", None)
    if tz:
        # set TZ envrionment variable to given tz param
        os.environ["TZ"] = tz
        time.tzset()

    # init logger using given params
    logger = Logger(service=f"{utc}-{datefmt}-{tz}", utc=utc, datefmt=datefmt)

    # return the converter this Logger is using
    if logger.handlers[0].formatter.converter == time.localtime:
        loggerType = "localtime_converter"
    elif logger.handlers[0].formatter.converter == time.gmtime:
        loggerType = "gmtime_converter"
    else:
        loggerType = "unknown"

    # print the message to Cloudwatch, timestamp included
    logger.info(loggerType)
    return "success"

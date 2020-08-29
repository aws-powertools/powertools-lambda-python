# -*- coding: utf-8 -*-
from aws_lambda_powertools.utilities.typing import LambdaClientContextMobileClient, LambdaDict


class LambdaClientContext(object):
    client: LambdaClientContextMobileClient
    custom: LambdaDict
    env: LambdaDict

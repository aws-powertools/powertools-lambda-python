import secrets

from aws_lambda_powertools import Logger


def get_random_logger(**kwargs):
    """Return vanilla logger w/ random name"""
    return Logger(name=secrets.token_urlsafe(), **kwargs)

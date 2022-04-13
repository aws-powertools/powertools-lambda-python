import boto3
import requests

from aws_lambda_powertools import Tracer

modules_to_be_patched = ["boto3", "requests"]
tracer = Tracer(patch_modules=modules_to_be_patched)

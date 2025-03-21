from __future__ import annotations

import os

from aws_lambda_powertools.shared import constants

is_cold_start = True

initialization_type = os.getenv(constants.LAMBDA_INITIALIZATION_TYPE)

# Check for Provisioned Concurrency environment
# AWS_LAMBDA_INITIALIZATION_TYPE is set when using Provisioned Concurrency
if initialization_type == "provisioned-concurrency":
    is_cold_start = False


def reset_cold_start_flag():
    global is_cold_start
    if not is_cold_start:
        is_cold_start = True

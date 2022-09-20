import sys

from aws_lambda_powertools import PACKAGE_PATH

PYTHON_RUNTIME_VERSION = f"V{''.join(map(str, sys.version_info[:2]))}"
SOURCE_CODE_ROOT_PATH = PACKAGE_PATH.parent
CDK_OUT_PATH = SOURCE_CODE_ROOT_PATH / "cdk.out"
LAYER_BUILD_PATH = CDK_OUT_PATH / "layer_build"

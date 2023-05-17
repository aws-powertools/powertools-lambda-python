import logging
import os
from sys import version_info

# Since Python 3.8 there is a built-in. Remove this when support for Python3.7 is dropped
# See https://docs.python.org/3/library/importlib.metadata.html
if version_info.major == 3 and version_info.minor == 7:
    from importlib_metadata import version
else:
    from importlib.metadata import version

powertools_version = version("aws-lambda-powertools")

try:
    from botocore import handlers
except ImportError:
    # if botocore failed to import, user might be using custom runtime. We can ignore here
    handlers = None

logger = logging.getLogger(__name__)

EXEC_ENV = os.environ.get("AWS_EXECUTION_ENV", "NA")
TARGET_SDK_EVENT = "request-created"
FEATURE_PREFIX = "PT"


# In case of no Powertools utility: PT/no-op/2.15.0 PTEnv/AWS_Lambda_python3.9
def _add_powertools_version(request, **kwargs):
    try:
        headers = request.headers
        headers["User-Agent"] = f"{headers['User-Agent']} {FEATURE_PREFIX}/no-op/{powertools_version} PTEnv/{EXEC_ENV}"
    except Exception:
        logger.debug("Missing header User-Agent")


# creates the `add_feature_string` function with given feature parameter
def _create_feature_function(feature):
    def add_powertools_feature(request, **kwargs):
        headers = request.headers
        # Actually, only one handler can be registered, registering a new one will replace the prev handler
        # We don't need to replace/detect previous registered user-agent
        headers[
            "User-Agent"
        ] = f"{headers['User-Agent']} {FEATURE_PREFIX}/{feature}/{powertools_version} PTEnv/{EXEC_ENV}"

    # return created function
    return add_powertools_feature


# add feature user-agent to given sdk boto3.session
def register_feature_to_session(session, feature):
    try:
        session.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# add feature user-agent to given sdk boto3.client
def register_feature_to_client(client, feature):
    try:
        client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# add feature user-agent to given sdk boto3.resource
def register_feature_to_resource(resource, feature):
    try:
        resource.meta.client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"resource passed in doesn't have a event system:{e}")


# register add_pt_version for all AWS SDK in runtime
def inject_user_agent():
    if handlers:
        # register add_user_agent to BUILTIN_HANDLERS so every aws sdk session will have this event registered
        handlers.BUILTIN_HANDLERS.append((TARGET_SDK_EVENT, _add_powertools_version))

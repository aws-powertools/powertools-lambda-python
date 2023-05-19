import logging
import os

from aws_lambda_powertools.shared.version import VERSION

powertools_version = VERSION
inject_header = True

try:
    import botocore
except ImportError:
    # if botocore failed to import, user might be using custom runtime and we can't inject header
    inject_header = False

logger = logging.getLogger(__name__)

EXEC_ENV: str = os.environ.get("AWS_EXECUTION_ENV", "NA")
TARGET_SDK_EVENT: str = "request-created"
FEATURE_PREFIX: str = "PT"
DEFAULT_FEATURE: str = "no-op"
HEADER_NO_OP: str = f"{FEATURE_PREFIX}/{DEFAULT_FEATURE}/{powertools_version} PTEnv/{EXEC_ENV}"


def _initializer_botocore_session(session):
    try:
        session.register(TARGET_SDK_EVENT, _create_feature_function(DEFAULT_FEATURE))
    except Exception:
        logger.debug("Can't add extra header User-Agent")


def _create_feature_function(feature):
    def add_powertools_feature(request, **kwargs):
        try:
            headers = request.headers
            header_user_agent: str = (
                f"{headers['User-Agent']} {FEATURE_PREFIX}/{feature}/{powertools_version} PTEnv/{EXEC_ENV}"
            )

            # This function is exclusive to client and resources objects created in Powertools
            # and must remove the no-op header, if present
            if HEADER_NO_OP in headers["User-Agent"] and feature != DEFAULT_FEATURE:
                # Remove HEADER_NO_OP + space
                header_user_agent = header_user_agent.replace(f"{HEADER_NO_OP} ", "")

            headers["User-Agent"] = f"{header_user_agent}"
        except Exception:
            logger.debug("Can't find User-Agent header")

    return add_powertools_feature


# Add feature user-agent to given sdk boto3.session
def register_feature_to_session(session, feature):
    try:
        session.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# Add feature user-agent to given sdk boto3.client
def register_feature_to_client(client, feature):
    try:
        client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# Add feature user-agent to given sdk boto3.resource
def register_feature_to_resource(resource, feature):
    try:
        resource.meta.client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"resource passed in doesn't have a event system:{e}")


def inject_user_agent():
    if inject_header:
        # Customize botocore session to inject Powertools header
        # See: https://github.com/boto/botocore/pull/2682
        botocore.register_initializer(_initializer_botocore_session)

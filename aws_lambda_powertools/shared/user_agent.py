import logging
import os

from importlib_metadata import version

pt_version = version("aws-lambda-powertools")

try:
    from botocore import handlers
except ImportError:
    # if botocore failed to import, user might be using custom runtime. We can ignore here
    handlers = None

logger = logging.getLogger(__name__)

ENV_KEY = "AWS_EXECUTION_ENV"
EXEC_ENV = os.environ.get(ENV_KEY, "NA")
target_sdk_event = "request-created"


# add user-agent like powertools/2.14.1 EXEC-ENV/AWS_Lambda_python3.9
def _add_pt_version(request, **kwargs):
    headers = request.headers
    # assume we always have a User-Agent.
    # Q: do we need to check if field: User-Agent exist in request.headers?
    # Q: do we care if User-Agent string exceed 256 characters?
    headers["User-Agent"] = f"{headers['User-Agent']} PT/no-op/{pt_version} PTEnv/{EXEC_ENV}"


# creates the `add_feature_string` function with given feature parameter
def _create_feature_function(feature):
    def add_pt_feature(request, **kwargs):
        headers = request.headers
        # Actually, only one handler can be registered, registering a new one will replace the prev handler
        # We don't need to replace/detect previous registered user-agent
        headers["User-Agent"] = f"{headers['User-Agent']} PT/{feature}/{pt_version} PTEnv/{EXEC_ENV}"

    # return created function
    return add_pt_feature


# add feature user-agent to given sdk session
def register_feature_to_session(session, feature):
    try:
        session.events.register(target_sdk_event, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# add feature user-agent to given sdk client
def register_feature_to_client(client, feature):
    try:
        client.meta.events.register(target_sdk_event, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# add feature user-agent to given sdk session.resource
def register_feature_to_resource(resource, feature):
    try:
        resource.meta.client.meta.events.register(target_sdk_event, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"resource passed in doesn't have a event system:{e}")


# register add_pt_version for all AWS SDK in runtime
def inject_user_agent():
    if handlers:
        # register add_user_agent to BUILTIN_HANDLERS so every aws sdk session will have this event registered
        handlers.BUILTIN_HANDLERS.append((target_sdk_event, _add_pt_version))

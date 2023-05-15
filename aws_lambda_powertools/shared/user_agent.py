import os

from importlib_metadata import version

pt_version = version("aws-lambda-powertools")

try:
    import botocore.handlers
except ImportError:
    # if botocore failed to import, user might be using custom runtime. We can ignore here
    botocore = None


ENV_KEY = "AWS_EXECUTION_ENV"
EXEC_ENV = os.environ.get(ENV_KEY, "NA")
target_sdk_event = "request-created"


# add user-agent like powertools/2.14.1 EXEC-ENV/AWS_Lambda_python3.9
def _add_pt_version(request, **kwargs):
    headers = request.headers
    if "PT/" not in headers:
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
        """
        # replace existing no-op user-agent with feature
        if "PT/no-op" in headers["User-Agent"]:
            headers["User-Agent"] = headers['User-Agent'].replace("PT/no-op", f"PT/{feature}")
            return
        # already registered, exit
        if f"PT/{feature}/" in headers["User-Agent"]:
            return
        # other feature registered, append
        # Q: do we want this? or replace the original feature?
        if "PT/" in headers["User-Agent"]:
            headers["User-Agent"] = f"{headers['User-Agent']} PT/{feature}/{pt_version}"
            return"""

        # no PT header found, insert new one
        headers["User-Agent"] = f"{headers['User-Agent']} PT/{feature}/{pt_version} PTEnv/{EXEC_ENV}"

    # return created function
    return add_pt_feature


# add feature user-agent to given sdk session
def register_feature_to_session(session, feature):
    session.events.register(target_sdk_event, _create_feature_function(feature))


# add feature user-agent to given sdk client
def register_feature_to_client(client, feature):
    client.meta.events.register(target_sdk_event, _create_feature_function(feature))


# register add_pt_version for all AWS SDK in runtime
def inject_user_agent():
    if botocore:
        # register add_user_agent to BUILTIN_HANDLERS so every aws sdk session will have this event registered
        botocore.handlers.BUILTIN_HANDLERS.append((target_sdk_event, _add_pt_version))

try:
    import botocore.handlers
except ImportError:
    botocore = None

try:
    import pkg_resources

    # there should be a more elegant way to get module version and feature version
    pt_version = pkg_resources.get_distribution("aws_lambda_powertools").version
except ImportError:
    pkg_resources = None
    # Not available
    pt_version = "NA"
import os

ENV_KEY = "AWS_EXECUTION_ENV"
EXEC_ENV = os.environ.get(ENV_KEY, "NA")


# add user-agent like powertools/2.14.1 EXEC-ENV/AWS_Lambda_python3.9
def add_user_agent(request, **kwargs):
    headers = request.headers
    headers["User-Agent"] = f"{headers['User-Agent']} powertools/{pt_version} EXEC-ENV/{EXEC_ENV}"


def register_user_agent():
    if botocore:
        # register add_user_agent to BUILTIN_HANDLERS so every aws sdk session will have this event registered
        botocore.handlers.BUILTIN_HANDLERS.append(("request-created", add_user_agent))

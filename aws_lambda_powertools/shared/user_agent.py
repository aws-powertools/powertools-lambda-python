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

EXEC_ENV = os.environ.get("AWS_EXECUTION_ENV", "NA")
TARGET_SDK_EVENT = "request-created"
FEATURE_PREFIX = "PT"
DEFAULT_FEATURE = "no-op"
HEADER_NO_OP = f"{FEATURE_PREFIX}/{DEFAULT_FEATURE}/{powertools_version} PTEnv/{EXEC_ENV}"


def _initializer_botocore_session(session):
    """
    This function is used to add an extra header for the User-Agent in the Botocore session,
    as described in the pull request: https://github.com/boto/botocore/pull/2682

    Parameters
    ----------
    session : botocore.session.Session
        The Botocore session to which the user-agent function will be registered.

    Raises
    ------
    Exception
        If there is an issue while adding the extra header for the User-Agent.

    """
    try:
        session.register(TARGET_SDK_EVENT, _create_feature_function(DEFAULT_FEATURE))
    except Exception:
        logger.debug("Can't add extra header User-Agent")


def _create_feature_function(feature):
    """
    Create and return the `add_powertools_feature` function.

    The `add_powertools_feature` function is designed to be registered in boto3's event system.
    When registered, it appends the given feature string to the User-Agent header of AWS SDK requests.

    Parameters
    ----------
    feature : str
        The feature string to be appended to the User-Agent header.

    Returns
    -------
    add_powertools_feature : Callable
        The `add_powertools_feature` function that modifies the User-Agent header.


    """

    def add_powertools_feature(request, **kwargs):
        try:
            headers = request.headers
            header_user_agent = (
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
    """
    Register the given feature string to the event system of the provided boto3 session
    and append the feature to the User-Agent header of the request

    Parameters
    ----------
    session : boto3.session.Session
        The boto3 session to which the feature will be registered.
    feature : str
        The feature string to be appended to the User-Agent header, e.g., "streaming" in Powertools.

    Raises
    ------
    AttributeError
        If the provided session does not have an event system.

    """
    try:
        session.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# Add feature user-agent to given sdk botocore.session.Session
def register_feature_to_botocore_session(botocore_session, feature):
    """
    Register the given feature string to the event system of the provided botocore session

    Please notice this function is for patching botocore session and is different from
    previous one which is for patching boto3 session

    Parameters
    ----------
    botocore_session : botocore.session.Session
        The botocore session to which the feature will be registered.
    feature : str
        The feature string to be appended to the User-Agent header, e.g., "data-masking" in Powertools.

    Raises
    ------
    AttributeError
        If the provided session does not have an event system.

    Examples
    --------
    **register data-masking user-agent to botocore session**

        >>> from aws_lambda_powertools.shared.user_agent import (
        >>>    register_feature_to_botocore_session
        >>> )
        >>>
        >>> session = botocore.session.Session()
        >>> register_feature_to_botocore_session(botocore_session=session, feature="data-masking")
        >>> key_provider = StrictAwsKmsMasterKeyProvider(key_ids=self.keys, botocore_session=session)

    """
    try:
        botocore_session.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"botocore session passed in doesn't have a event system:{e}")


# Add feature user-agent to given sdk boto3.client
def register_feature_to_client(client, feature):
    """
    Register the given feature string to the event system of the provided boto3 client
    and append the feature to the User-Agent header of the request

    Parameters
    ----------
    client : boto3.session.Session.client
        The boto3 client to which the feature will be registered.
    feature : str
        The feature string to be appended to the User-Agent header, e.g., "streaming" in Powertools.

    Raises
    ------
    AttributeError
        If the provided client does not have an event system.

    """
    try:
        client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"session passed in doesn't have a event system:{e}")


# Add feature user-agent to given sdk boto3.resource
def register_feature_to_resource(resource, feature):
    """
    Register the given feature string to the event system of the provided boto3 resource
    and append the feature to the User-Agent header of the request

    Parameters
    ----------
    resource : boto3.session.Session.resource
        The boto3 resource to which the feature will be registered.
    feature : str
        The feature string to be appended to the User-Agent header, e.g., "streaming" in Powertools.

    Raises
    ------
    AttributeError
        If the provided resource does not have an event system.

    """
    try:
        resource.meta.client.meta.events.register(TARGET_SDK_EVENT, _create_feature_function(feature))
    except AttributeError as e:
        logger.debug(f"resource passed in doesn't have a event system:{e}")


def inject_user_agent():
    if inject_header:
        # Some older botocore versions doesn't support register_initializer. In those cases, we disable the feature.
        if not hasattr(botocore, "register_initializer"):
            return

        # Customize botocore session to inject Powertools header
        # See: https://github.com/boto/botocore/pull/2682
        botocore.register_initializer(_initializer_botocore_session)

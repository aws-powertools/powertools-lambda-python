from typing import Dict, Optional, overload

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.data_classes.shared_functions import (
    get_header_value,
)


class S3ObjectContext(DictWrapper):
    """The input and output details for connections to Amazon S3 and S3 Object Lambda."""

    @property
    def input_s3_url(self) -> str:
        """A pre-signed URL that can be used to fetch the original object from Amazon S3.

        The URL is signed using the original caller’s identity, and their permissions
        will apply when the URL is used. If there are signed headers in the URL, the
        Lambda function must include these in the call to Amazon S3, except for the Host."""
        return self["inputS3Url"]

    @property
    def output_route(self) -> str:
        """A routing token that is added to the S3 Object Lambda URL when the Lambda function
        calls `WriteGetObjectResponse`."""
        return self["outputRoute"]

    @property
    def output_token(self) -> str:
        """An opaque token used by S3 Object Lambda to match the WriteGetObjectResponse call
        with the original caller."""
        return self["outputToken"]


class S3ObjectConfiguration(DictWrapper):
    """Configuration information about the S3 Object Lambda access point."""

    @property
    def access_point_arn(self) -> str:
        """The Amazon Resource Name (ARN) of the S3 Object Lambda access point that received
        this request."""
        return self["accessPointArn"]

    @property
    def supporting_access_point_arn(self) -> str:
        """The ARN of the supporting access point that is specified in the S3 Object Lambda
        access point configuration."""
        return self["supportingAccessPointArn"]

    @property
    def payload(self) -> str:
        """Custom data that is applied to the S3 Object Lambda access point configuration.

        S3 Object Lambda treats this as an opaque string, so it might need to be decoded
        before use."""
        return self["payload"]


class S3ObjectUserRequest(DictWrapper):
    """Information about the original call to S3 Object Lambda."""

    @property
    def url(self) -> str:
        """The decoded URL of the request as received by S3 Object Lambda, excluding any
        authorization-related query parameters."""
        return self["url"]

    @property
    def headers(self) -> Dict[str, str]:
        """A map of string to strings containing the HTTP headers and their values from the original call,
        excluding any authorization-related headers.

        If the same header appears multiple times, their values are combined into a comma-delimited list.
        The case of the original headers is retained in this map."""
        return self["headers"]

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: str,
        case_sensitive: bool = False,
    ) -> str: ...

    @overload
    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> Optional[str]: ...

    def get_header_value(
        self,
        name: str,
        default_value: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> Optional[str]:
        """Get header value by name

        Parameters
        ----------
        name: str
            Header name
        default_value: str, optional
            Default value if no value was found by name
        case_sensitive: bool
            Whether to use a case-sensitive look up
        Returns
        -------
        str, optional
            Header value
        """
        return get_header_value(self.headers, name, default_value, case_sensitive)


class S3ObjectSessionIssuer(DictWrapper):
    @property
    def get_type(self) -> str:
        """The source of the temporary security credentials, such as Root, IAMUser, or Role."""
        return self["type"]

    @property
    def user_name(self) -> str:
        """The friendly name of the user or role that issued the session."""
        return self["userName"]

    @property
    def principal_id(self) -> str:
        """The internal ID of the entity that was used to get credentials."""
        return self["principalId"]

    @property
    def arn(self) -> str:
        """The ARN of the source (account, IAM user, or role) that was used to get temporary security credentials."""
        return self["arn"]

    @property
    def account_id(self) -> str:
        """The account that owns the entity that was used to get credentials."""
        return self["accountId"]


class S3ObjectSessionAttributes(DictWrapper):
    @property
    def creation_date(self) -> str:
        """The date and time when the temporary security credentials were issued.
        Represented in ISO 8601 basic notation."""
        return self["creationDate"]

    @property
    def mfa_authenticated(self) -> str:
        """The value is true if the root user or IAM user whose credentials were used for the request also was
        authenticated with an MFA device; otherwise, false."""
        return self["mfaAuthenticated"]


class S3ObjectSessionContext(DictWrapper):
    @property
    def session_issuer(self) -> S3ObjectSessionIssuer:
        """If the request was made with temporary security credentials, an element that provides information
        about how the credentials were obtained."""
        return S3ObjectSessionIssuer(self["sessionIssuer"])

    @property
    def attributes(self) -> S3ObjectSessionAttributes:
        """Session attributes."""
        return S3ObjectSessionAttributes(self["attributes"])


class S3ObjectUserIdentity(DictWrapper):
    """Details about the identity that made the call to S3 Object Lambda.

    Documentation:
    -------------
    - https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html
    """

    @property
    def get_type(self) -> str:
        """The type of identity.

        The following values are possible:

        - Root – The request was made with your AWS account credentials. If the userIdentity
          type is Root and you set an alias for your account, the userName field contains your account alias.
          For more information, see Your AWS Account ID and Its Alias.
        - IAMUser – The request was made with the credentials of an IAM user.
        - AssumedRole – The request was made with temporary security credentials that were obtained
          with a role via a call to the AWS Security Token Service (AWS STS) AssumeRole API. This can include
          roles for Amazon EC2 and cross-account API access.
        - FederatedUser – The request was made with temporary security credentials that were obtained via a
          call to the AWS STS GetFederationToken API. The sessionIssuer element indicates if the API was
          called with root or IAM user credentials.
        - AWSAccount – The request was made by another AWS account.
        -  AWSService – The request was made by an AWS account that belongs to an AWS service.
          For example, AWS Elastic Beanstalk assumes an IAM role in your account to call other AWS services
          on your behalf.
        """
        return self["type"]

    @property
    def account_id(self) -> str:
        """The account that owns the entity that granted permissions for the request.

        If the request was made with temporary security credentials, this is the account that owns the IAM
        user or role that was used to obtain credentials."""
        return self["accountId"]

    @property
    def access_key_id(self) -> str:
        """The access key ID that was used to sign the request.

        If the request was made with temporary security credentials, this is the access key ID of
        the temporary credentials. For security reasons, accessKeyId might not be present, or might
        be displayed as an empty string."""
        return self["accessKeyId"]

    @property
    def user_name(self) -> str:
        """The friendly name of the identity that made the call."""
        return self["userName"]

    @property
    def principal_id(self) -> str:
        """The unique identifier for the identity that made the call.

        For requests made with temporary security credentials, this value includes
        the session name that is passed to the AssumeRole, AssumeRoleWithWebIdentity,
        or GetFederationToken API call."""
        return self["principalId"]

    @property
    def arn(self) -> str:
        """The ARN of the principal that made the call.
        The last section of the ARN contains the user or role that made the call."""
        return self["arn"]

    @property
    def session_context(self) -> Optional[S3ObjectSessionContext]:
        """If the request was made with temporary security credentials,
        this element provides information about the session that was created for those credentials."""
        session_context = self.get("sessionContext")

        if session_context is None:
            return None

        return S3ObjectSessionContext(session_context)


class S3ObjectLambdaEvent(DictWrapper):
    """S3 object lambda event

    Documentation:
    -------------
    - https://docs.aws.amazon.com/AmazonS3/latest/userguide/olap-writing-lambda.html

    Example
    -------
    **Fetch and transform original object from Amazon S3**

        import boto3
        import requests
        from aws_lambda_powertools.utilities.data_classes.s3_object_event import S3ObjectLambdaEvent

        session = boto3.Session()
        s3 = session.client("s3")

        def lambda_handler(event, context):
            event = S3ObjectLambdaEvent(event)

            # Get object from S3
            response = requests.get(event.input_s3_url)
            original_object = response.content.decode("utf-8")

            # Make changes to the object about to be returned
            transformed_object = original_object.upper()

            # Write object back to S3 Object Lambda
            s3.write_get_object_response(
                Body=transformed_object, RequestRoute=event.request_route, RequestToken=event.request_token
            )
    """

    @property
    def request_id(self) -> str:
        """The Amazon S3 request ID for this request. We recommend that you log this value to help with debugging."""
        return self["xAmzRequestId"]

    @property
    def object_context(self) -> S3ObjectContext:
        """The input and output details for connections to Amazon S3 and S3 Object Lambda."""
        return S3ObjectContext(self["getObjectContext"])

    @property
    def configuration(self) -> S3ObjectConfiguration:
        """Configuration information about the S3 Object Lambda access point."""
        return S3ObjectConfiguration(self["configuration"])

    @property
    def user_request(self) -> S3ObjectUserRequest:
        """Information about the original call to S3 Object Lambda."""
        return S3ObjectUserRequest(self["userRequest"])

    @property
    def user_identity(self) -> S3ObjectUserIdentity:
        """Details about the identity that made the call to S3 Object Lambda."""
        return S3ObjectUserIdentity(self["userIdentity"])

    @property
    def request_route(self) -> str:
        """A routing token that is added to the S3 Object Lambda URL when the Lambda function
        calls `WriteGetObjectResponse`."""
        return self.object_context.output_route

    @property
    def request_token(self) -> str:
        """An opaque token used by S3 Object Lambda to match the WriteGetObjectResponse call
        with the original caller."""
        return self.object_context.output_token

    @property
    def input_s3_url(self) -> str:
        """A pre-signed URL that can be used to fetch the original object from Amazon S3.

        The URL is signed using the original caller’s identity, and their permissions
        will apply when the URL is used. If there are signed headers in the URL, the
        Lambda function must include these in the call to Amazon S3, except for the Host.

        Example
        -------
        **Fetch original object from Amazon S3**

            import requests
            from aws_lambda_powertools.utilities.data_classes.s3_object_event import S3ObjectLambdaEvent

            def lambda_handler(event, context):
                event = S3ObjectLambdaEvent(event)

                response = requests.get(event.input_s3_url)
                original_object = response.content.decode("utf-8")
                ...
        """
        return self.object_context.input_s3_url

    @property
    def protocol_version(self) -> str:
        """The version ID of the context provided.

        The format of this field is `{Major Version}`.`{Minor Version}`.
        The minor version numbers are always two-digit numbers. Any removal or change to the semantics of a
        field will necessitate a major version bump and will require active opt-in. Amazon S3 can add new
        fields at any time, at which point you might experience a minor version bump. Due to the nature of
        software rollouts, it is possible that you might see multiple minor versions in use at once.
        """
        return self["protocolVersion"]

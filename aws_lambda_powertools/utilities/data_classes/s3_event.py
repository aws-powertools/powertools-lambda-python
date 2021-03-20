from typing import Any, Dict, Iterator, Optional
from urllib.parse import unquote_plus

from aws_lambda_powertools.utilities.data_classes.common import DictWrapper


class S3Identity(DictWrapper):
    @property
    def principal_id(self) -> str:
        return self["principalId"]


class S3RequestParameters(DictWrapper):
    @property
    def source_ip_address(self) -> str:
        return self["requestParameters"]["sourceIPAddress"]


class S3Bucket(DictWrapper):
    @property
    def name(self) -> str:
        return self["s3"]["bucket"]["name"]

    @property
    def owner_identity(self) -> S3Identity:
        return S3Identity(self["s3"]["bucket"]["ownerIdentity"])

    @property
    def arn(self) -> str:
        return self["s3"]["bucket"]["arn"]


class S3Object(DictWrapper):
    @property
    def key(self) -> str:
        """Object key"""
        return self["s3"]["object"]["key"]

    @property
    def size(self) -> int:
        """Object byte size"""
        return int(self["s3"]["object"]["size"])

    @property
    def etag(self) -> str:
        """object eTag"""
        return self["s3"]["object"]["eTag"]

    @property
    def version_id(self) -> Optional[str]:
        """Object version if bucket is versioning-enabled, otherwise null"""
        return self["s3"]["object"].get("versionId")

    @property
    def sequencer(self) -> str:
        """A string representation of a hexadecimal value used to determine event sequence,
        only used with PUTs and DELETEs
        """
        return self["s3"]["object"]["sequencer"]


class S3Message(DictWrapper):
    @property
    def s3_schema_version(self) -> str:
        return self["s3"]["s3SchemaVersion"]

    @property
    def configuration_id(self) -> str:
        """ID found in the bucket notification configuration"""
        return self["s3"]["configurationId"]

    @property
    def bucket(self) -> S3Bucket:
        return S3Bucket(self._data)

    @property
    def get_object(self) -> S3Object:
        """Get the `object` property as an S3Object"""
        # Note: this name conflicts with existing python builtins
        return S3Object(self._data)


class S3EventRecordGlacierRestoreEventData(DictWrapper):
    @property
    def lifecycle_restoration_expiry_time(self) -> str:
        """Time when the object restoration will be expired."""
        return self["restoreEventData"]["lifecycleRestorationExpiryTime"]

    @property
    def lifecycle_restore_storage_class(self) -> str:
        """Source storage class for restore"""
        return self["restoreEventData"]["lifecycleRestoreStorageClass"]


class S3EventRecordGlacierEventData(DictWrapper):
    @property
    def restore_event_data(self) -> S3EventRecordGlacierRestoreEventData:
        """The restoreEventData key contains attributes related to your restore request.

        The glacierEventData key is only visible for s3:ObjectRestore:Completed events
        """
        return S3EventRecordGlacierRestoreEventData(self._data)


class S3EventRecord(DictWrapper):
    @property
    def event_version(self) -> str:
        """The eventVersion key value contains a major and minor version in the form <major>.<minor>."""
        return self["eventVersion"]

    @property
    def event_source(self) -> str:
        """The AWS service from which the S3 event originated. For S3, this is aws:s3"""
        return self["eventSource"]

    @property
    def aws_region(self) -> str:
        """aws region eg: us-east-1"""
        return self["awsRegion"]

    @property
    def event_time(self) -> str:
        """The time, in ISO-8601 format, for example, 1970-01-01T00:00:00.000Z, when S3 finished
        processing the request"""
        return self["eventTime"]

    @property
    def event_name(self) -> str:
        """Event type"""
        return self["eventName"]

    @property
    def user_identity(self) -> S3Identity:
        return S3Identity(self["userIdentity"])

    @property
    def request_parameters(self) -> S3RequestParameters:
        return S3RequestParameters(self._data)

    @property
    def response_elements(self) -> Dict[str, str]:
        """The responseElements key value is useful if you want to trace a request by following up with AWS Support.

        Both x-amz-request-id and x-amz-id-2 help Amazon S3 trace an individual request. These values are the same
        as those that Amazon S3 returns in the response to the request that initiates the events, so they can be
        used to match the event to the request.
        """
        return self["responseElements"]

    @property
    def s3(self) -> S3Message:
        return S3Message(self._data)

    @property
    def glacier_event_data(self) -> Optional[S3EventRecordGlacierEventData]:
        """The glacierEventData key is only visible for s3:ObjectRestore:Completed events."""
        item = self.get("glacierEventData")
        return None if item is None else S3EventRecordGlacierEventData(item)


class S3Event(DictWrapper):
    """S3 event notification

    Documentation:
    -------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html
    - https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html
    - https://docs.aws.amazon.com/AmazonS3/latest/dev/notification-content-structure.html
    """

    @property
    def records(self) -> Iterator[S3EventRecord]:
        for record in self["Records"]:
            yield S3EventRecord(record)

    @property
    def record(self) -> S3EventRecord:
        """Get the first s3 event record"""
        return next(self.records)

    @property
    def bucket_name(self) -> str:
        """Get the bucket name for the first s3 event record"""
        return self["Records"][0]["s3"]["bucket"]["name"]

    @property
    def object_key(self) -> str:
        """Get the object key for the first s3 event record and unquote plus"""
        return unquote_plus(self["Records"][0]["s3"]["object"]["key"])


class S3ObjectContext(DictWrapper):
    """The input and output details for connections to Amazon S3 and S3 Object Lambda."""

    @property
    def input_s3_url(self) -> str:
        """A presigned URL that can be used to fetch the original object from Amazon S3.
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
    """ Information about the original call to S3 Object Lambda."""

    @property
    def url(self) -> str:
        """The decoded URL of the request as received by S3 Object Lambda, excluding any
        authorization-related query parameters."""
        return self["url"]

    @property
    def headers(self) -> Dict[str, str]:
        """A map of string to strings containing the HTTP headers and their values from the
        original call, excluding any authorization-related headers. If the same header appears
        multiple times, their values are combined into a comma-delimited list. The case of the
        original headers is retained in this map."""
        return self["headers"]


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
    def session_context(self) -> Optional[Dict[str, Any]]:
        """ If the request was made with temporary security credentials,
        this element provides information about the session that was created for those credentials."""
        return self.get("sessionContext")


class S3ObjectEvent(DictWrapper):
    """S3 object event notification

    Documentation:
    -------------
    - https://docs.aws.amazon.com/AmazonS3/latest/userguide/olap-writing-lambda.html
    """

    @property
    def request_id(self) -> str:
        """The Amazon S3 request ID for this request. We recommend that you log this value to help with debugging."""
        return self["xAmzRequestId"]

    def object_context(self) -> S3ObjectContext:
        """The input and output details for connections to Amazon S3 and S3 Object Lambda."""
        return S3ObjectContext(self["getObjectContext"])

    def configuration(self) -> S3ObjectConfiguration:
        """Configuration information about the S3 Object Lambda access point."""
        return S3ObjectConfiguration(self["configuration"])

    def user_request(self) -> S3ObjectUserRequest:
        """Information about the original call to S3 Object Lambda."""
        return S3ObjectUserRequest(self["userRequest"])

    def user_identity(self) -> S3ObjectUserIdentity:
        """Details about the identity that made the call to S3 Object Lambda."""
        return S3ObjectUserIdentity(self["userIdentity"])

    def protocol_version(self) -> str:
        """The version ID of the context provided.
        The format of this field is {Major Version}.{Minor Version}.
        The minor version numbers are always two-digit numbers. Any removal or change to the semantics of a
        field will necessitate a major version bump and will require active opt-in. Amazon S3 can add new
        fields at any time, at which point you might experience a minor version bump. Due to the nature of
        software rollouts, it is possible that you might see multiple minor versions in use at once.
        """
        return self["protocolVersion"]

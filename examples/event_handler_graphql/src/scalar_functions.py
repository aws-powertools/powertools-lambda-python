from aws_lambda_powertools.utilities.data_classes.appsync.scalar_types_utils import (
    aws_date,
    aws_datetime,
    aws_time,
    aws_timestamp,
    make_id,
)

# Scalars: https://docs.aws.amazon.com/appsync/latest/devguide/scalars.html

_: str = make_id()  # Scalar: ID!
_: str = aws_date()  # Scalar: AWSDate
_: str = aws_time()  # Scalar: AWSTime
_: str = aws_datetime()  # Scalar: AWSDateTime
_: int = aws_timestamp()  # Scalar: AWSTimestamp

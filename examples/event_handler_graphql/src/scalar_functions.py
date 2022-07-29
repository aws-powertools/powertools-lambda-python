from aws_lambda_powertools.utilities.data_classes.appsync.scalar_types_utils import (
    aws_date,
    aws_datetime,
    aws_time,
    aws_timestamp,
    make_id,
)

# Scalars: https://docs.aws.amazon.com/appsync/latest/devguide/scalars.html

my_id: str = make_id()  # Scalar: ID!
my_date: str = aws_date()  # Scalar: AWSDate
my_timestamp: str = aws_time()  # Scalar: AWSTime
my_datetime: str = aws_datetime()  # Scalar: AWSDateTime
my_epoch_timestamp: int = aws_timestamp()  # Scalar: AWSTimestamp

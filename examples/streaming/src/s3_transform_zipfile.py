from aws_lambda_powertools.utilities.streaming import S3Object
from aws_lambda_powertools.utilities.streaming.transformations import ZipTransform

s3object = S3Object(bucket="bucket", key="key")
zip_reader = s3object.transform(ZipTransform())
with zip_reader.open("filename.txt") as f:
    for line in f:
        print(line)

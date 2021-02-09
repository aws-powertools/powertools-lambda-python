# Cold Start Benchmark

The [benchmark.sh script](./benchmark.sh) is a bash script to compare the cold-start time of using the AWS Lambda Powertools in a semi-automated way. It does so by deploying two Lambda functions which both have the aws-lambda-powertools module installed. One Lambda function will import and initialize the three core utilities (`Metrics`, `Logger`, `Tracer`), while the other one will not.

Please note that this requires the [SAM CLI](https://github.com/aws/aws-sam-cli) version 1.2.0 or later.

## Usage

> **NOTE**: This script is expected to run in Unix-based systems only, and can incur charges on your AWS account.

To use the script, you should move into the benchmark folder and run the benchmark script:

```
export S3_BUCKET=code-artifact-s3-bucket

cd benchmark
./benchmark.sh
```

This will:

* Deploy a CloudFormation stack using guided SAM deployment (*you will need to answer a few questions*).
* Run loops to update the memory setting of the functions to force a cold start, then invoke them. This process is repeated a number of time to get more consistent results.
* Wait 2.5 minutes to ensure data propagates from CloudWatch Logs to CloudWatch Logs Insights.
* Run a query on CloudWatch Logs insights, looking at the **REPORT** line from the logs.
* Delete the CloudFormation stack.

#!/bin/bash

set -e
trap cleanup EXIT

if [ -z "S3_BUCKET" ]; then
    echo "Missing S3_BUCKET environment variabe"
    exit 1
fi

export BENCHMARK_STACK_NAME=${BENCHMARK_STACK_NAME:-"powertools-benchmark"}

function cleanup {
    echo "Cleaning up stack..."
    aws cloudformation delete-stack --stack-name $BENCHMARK_STACK_NAME
}

function run_function {
    # Update function to force a cold start
    aws lambda update-function-configuration --function-name $1 --memory-size 256 >/dev/null
    aws lambda update-function-configuration --function-name $1 --memory-size 128 >/dev/null
    # Cold-start invoke
    aws lambda invoke --function-name $1 --payload '{}' /dev/null >/dev/null && echo -n . || echo -n e
}

# Retrieve statistics
function get_stats {
    # Gather results from CloudWatch Logs Insights
    query_id=$(aws logs start-query --log-group-name $1 --query-string 'filter @type = "REPORT" | stats pct(@initDuration, 50) as init_duration, pct(@duration, 50) as duration' --start-time $(expr $(date +%s) - 86400) --end-time $(expr $(date +%s) + 0) --query 'queryId' --output text)
    while true; do
        result=$(aws logs get-query-results --query-id $query_id --query 'status' --output text)
        if [ $result == "Complete" ]; then
            break
        fi
        sleep 1
    done

    # Check if greater than threshold and print result
    init_duration=$(aws logs get-query-results --query-id $query_id --query 'results[0][?field==`init_duration`].value' --output text)
    duration=$(aws logs get-query-results --query-id $query_id --query 'results[0][?field==`duration`].value' --output text)
    echo "$init_duration,$duration"
}

# Build and deploy the benchmark stack
echo "Building and deploying..."
sam build
sam deploy --stack-name $BENCHMARK_STACK_NAME --s3-bucket $S3_BUCKET --capabilities CAPABILITY_IAM

# Retrieve output values
echo "Retrieve values..."
export INSTRUMENTED_FUNCTION=$(aws cloudformation describe-stacks --stack-name $BENCHMARK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`InstrumentedFunction`].OutputValue' --output text)
export REFERENCE_FUNCTION=$(aws cloudformation describe-stacks --stack-name $BENCHMARK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ReferenceFunction`].OutputValue' --output text)
export INSTRUMENTED_LOG_GROUP=$(aws cloudformation describe-stacks --stack-name $BENCHMARK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`InstrumentedLogGroup`].OutputValue' --output text)
export REFERENCE_LOG_GROUP=$(aws cloudformation describe-stacks --stack-name $BENCHMARK_STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ReferenceLogGroup`].OutputValue' --output text)

echo INSTRUMENTED_FUNCTION=$INSTRUMENTED_FUNCTION
echo REFERENCE_FUNCTION=$REFERENCE_FUNCTION
echo INSTRUMENTED_LOG_GROUP=$INSTRUMENTED_LOG_GROUP
echo REFERENCE_LOG_GROUP=$REFERENCE_LOG_GROUP

# Running cold starts
echo "Running functions..."
for i in {0..20}; do
    run_function $INSTRUMENTED_FUNCTION
done &
process_id=$!
for i in {0..20}; do
    run_function $REFERENCE_FUNCTION
done &
wait $process_id
wait $!
echo

# Gather statistics
# Waiting 2.5 minutes to make sure the data propagates from CloudWatch Logs
# into CloudWatch Logs Insights.
echo "Waiting for data to propagate in CloudWatch Logs Insights..."
sleep 150
return_code=0
echo "INSTRUMENTED=$(get_stats $INSTRUMENTED_LOG_GROUP)"
echo "REFERENCE=$(get_stats $REFERENCE_LOG_GROUP)"

exit $return_code

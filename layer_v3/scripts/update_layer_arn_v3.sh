#!/bin/bash

# This script is run during the publish_v3_layer.yml CI job,
# and it is responsible for replacing the layer ARN in our documentation.
# Our pipeline must generate the same layer number for all commercial regions + gov cloud
# If this doesn't happens, we have an error and we must fix it in the deployment.
#
# see .github/workflows/reusable_deploy_v3_layer_stack.yml


# Get the new version number from the first command-line argument
new_version=$1
if [ -z "$new_version" ]; then
    echo "Usage: $0 <new_version>"
    exit 1
fi

# Find all files with specified extensions in ./docs and ./examples directories
# -type f: only find files (not directories)
# \( ... \): group conditions
# -o: logical OR
# -print0: use null character as separator (handles filenames with spaces)
find ./docs ./examples -type f \( -name "*.md" -o -name "*.py" -o -name "*.yaml" -o -name "*.txt" -o -name "*.tf" -o -name "*.yml" \) -print0 | while IFS= read -r -d '' file; do
    echo "Processing file: $file"

    # Use sed to replace the version number in the Lambda layer ARN
    # -i: edit files in-place without creating a backup
    # -E: use extended regular expressions
    # The regex matches the layer name and replaces only the version number at the end
    sed -i -E "s/(AWSLambdaPowertoolsPythonV3-python[0-9]+-((arm64)|(x86_64)):)[0-9]+/\1$new_version/g" "$file"
    if [ $? -eq 0 ]; then
        echo "Updated $file successfully"
        grep "arn:aws:lambda:" "$file"
    else
        echo "Error processing $file"
    fi
done
echo "Layer version update attempt completed."

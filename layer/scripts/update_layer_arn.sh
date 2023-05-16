#!/bin/bash

# This script is run during the publish_v2_layer.yml CI job,
# and it is responsible for replacing the layer ARN in our documentation,
# based on the output files generated by CDK when deploying to each pseudo_region.
#
# see .github/workflows/reusable_deploy_v2_layer_stack.yml

set -eo pipefail
set -x

if [[ $# -ne 1 ]]; then
  cat <<EOM
Usage: $(basename $0) cdk-output-dir

cdk-output-dir: directory containing the cdk output files generated when deploying the Layer
EOM
  exit 1
fi

CDK_OUTPUT_DIR=$1

# Check if CDK output dir is a directory
if [ ! -d "$CDK_OUTPUT_DIR" ]; then
  echo "No $CDK_OUTPUT_DIR directory found, not replacing lambda layer versions"
  exit 1
fi

# Process each file inside the directory
files="$CDK_OUTPUT_DIR/*"
for file in $files; do
  echo "[+] Processing: $file"

  # Process each line inside the file
  lines=$(cat "$file")
  for line in $lines; do
    echo -e "\t[*] ARN: $line"
    # line = arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPython:49

    # From the full ARN, extract everything but the version at the end. This prefix
    # will later be used to find/replace the ARN on the documentation file.
    prefix=$(echo "$line" | cut -d ':' -f 1-7)
    # prefix = arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPython

    # Now replace the all "prefix"s in the file with the full new Layer ARN (line)
    # prefix:\d+ ==> line
    # sed doesn't support \d+ in a portable way, so we cheat with (:digit: :digit: *)
    sed -i -e "s/$prefix:[[:digit:]][[:digit:]]*/$line/g" docs/index.md

    # We use the eu-central-1 layer as the version for all the frameworks (SAM, CDK, SLS, etc)
    # We could have used any other region. What's important is the version at the end.

    # Examples of strings found in the documentation with pseudo regions:
    # arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPython:39
    # arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPython:39
    # arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPython:39
    # arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPython:39
    if [[ "$line" == *"eu-central-1"* ]]; then
      # These are all the framework pseudo parameters currently found in the docs
      for pseudo_region in '{region}' '${AWS::Region}' '${aws:region}' '{env.region}'; do
        prefix_pseudo_region=$(echo "$prefix" | sed "s/eu-central-1/${pseudo_region}/")
        # prefix_pseudo_region = arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPython

        line_pseudo_region=$(echo "$line" | sed "s/eu-central-1/${pseudo_region}/")
        # line_pseudo_region = arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPython:49

        # Replace all the "prefix_pseudo_region"'s in the file
        # prefix_pseudo_region:\d+ ==> line_pseudo_region
        sed -i -e "s/$prefix_pseudo_region:[[:digit:]][[:digit:]]*/$line_pseudo_region/g" docs/index.md

        # The same strings can also be found in examples on Logger, Tracer and Metrics
        sed -i -e "s/$prefix_pseudo_region:[[:digit:]][[:digit:]]*/$line_pseudo_region/g" examples/logger/sam/template.yaml
        sed -i -e "s/$prefix_pseudo_region:[[:digit:]][[:digit:]]*/$line_pseudo_region/g" examples/metrics/sam/template.yaml
        sed -i -e "s/$prefix_pseudo_region:[[:digit:]][[:digit:]]*/$line_pseudo_region/g" examples/tracer/sam/template.yaml
      done
    fi
  done
done

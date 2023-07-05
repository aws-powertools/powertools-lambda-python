# v1
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:a7eb0875e2d7e96eb7baab4f6104b077dd8d5a9aabcde40c9251f8ad33de0e36
COPY . $SRC/
WORKDIR $SRC/aws_lambda_powertools
COPY .clusterfuzzlite/build.sh $SRC/

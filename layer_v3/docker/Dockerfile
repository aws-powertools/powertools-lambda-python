# First stage: setting the base image
ARG PYTHON_VERSION=""

FROM public.ecr.aws/lambda/python:${PYTHON_VERSION} AS base_build

# Second stage: building the layer
FROM base_build

ARG PYTHON_VERSION=""
ARG PACKAGE_SUFFIX=""

USER root
WORKDIR /tmp

# PACKAGE_SUFFIX = '[all]==3.0.0'
# PACKAGE_SUFFIX = '[all] @ git+https://github.com/awslabs/aws-lambda-powertools-python@develop'
# PACKAGE_SUFFIX = '[all]'
# PACKAGE_SUFFIX = '=='3.0.0'
# PACKAGE_SUFFIX = ' @ git+https://github.com/awslabs/aws-lambda-powertools-python@develop'
# PACKAGE_SUFFIX = ''

# PYTHON_VERSION = 3.9, 3.10, 3.11, 3.12, and 3.13

# Installing libs based on base image; We must use dnf for AL2023 (Python 3.12+)
COPY install_libraries.sh .
RUN chmod a+x /tmp/install_libraries.sh
RUN /bin/sh /tmp/install_libraries.sh

# Install cython to generate native code
RUN pip install --upgrade pip wheel && pip install --upgrade cython
# Optimize binary size and strip debugging symbols for optimum size
RUN CFLAGS="-Os -g0 -s" pip install -t /asset/python "aws-lambda-powertools${PACKAGE_SUFFIX}"

# Removing nonessential files
RUN cd /asset/python && \
  # remove boto3 and botocore (already available in Lambda Runtime)
  rm -rf boto* && \
  # remove boto3 dependencies
  rm -rf s3transfer* *dateutil* urllib3* six* jmespath* && \
  # remove debugging symbols
  find . -name '*.so' -type f -exec strip "{}" \; && \
  # remove tests
  find . -wholename "*/tests/*" -type f -delete && \
  # remove python bytecode
  find . -regex '^.*\(__pycache__\|\.py[co]\)$' -delete

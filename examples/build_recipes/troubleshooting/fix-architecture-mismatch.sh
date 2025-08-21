#!/bin/bash
# Use Docker with Lambda base image
docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.13 \
    pip install aws-lambda-powertools[all] -t /var/task/

# Or force Linux-compatible wheels
pip install --platform manylinux2014_x86_64 --implementation cp \
    --python-version 3.13 --only-binary=:all: aws-lambda-powertools[all]

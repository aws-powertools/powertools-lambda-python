#!/bin/bash
# Use Amazon Linux 2 base image for builds
docker run --rm -v "$PWD":/var/task \
    public.ecr.aws/lambda/python:3.11 \
    pip install -r requirements.txt -t /var/task/

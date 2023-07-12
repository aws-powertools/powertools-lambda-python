# See here all gitpod images available: https://hub.docker.com/r/gitpod/workspace-python-3.9/tags
# Current python version: 3.9.13
FROM gitpod/workspace-python-3.9@sha256:de87d4ebffe8daab2e8fef96ec20497ae4f39e8dcb9dec1483d0be61ea78e8cd

WORKDIR /app
ADD . /app

# Installing pre-commit as system package and not user package. Git needs this to execute pre-commit hooks.
RUN export PIP_USER=no
# v3.3.3
RUN python3 -m pip install --require-hashes -r .gitpod_requirements.txt
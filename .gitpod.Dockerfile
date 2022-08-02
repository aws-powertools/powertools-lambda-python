# See here all gitpod images available: https://hub.docker.com/r/gitpod/workspace-python-3.10/tags
# Current python version: 3.10.5
FROM gitpod/workspace-python-3.10@sha256:8a7ad4f0bbaa281a36cf2a87b772354638a14d7383f0a755b9ea32596ee99632

WORKDIR /app
ADD . /app

# Installing pre-commit as system package and not user package. Git needs this to execute pre-commit hooks.
RUN export PIP_USER=no
RUN python3 -m pip install pre-commit

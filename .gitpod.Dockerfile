# See here all gitpod images available: https://hub.docker.com/r/gitpod/workspace-python-3.11/tags
# Current python version: 3.11.9
FROM gitpod/workspace-python-3.11@sha256:2d9a242844bef5710ab4622899a5254a0c59f0ac58c0d3ac998f749323f43951

WORKDIR /app
ADD . /app

# Installing pre-commit as system package and not user package. Git needs this to execute pre-commit hooks.
RUN export PIP_USER=no
# pre-commit v3.7.1
RUN python3 -m pip install --require-hashes -r .gitpod_requirements.txt
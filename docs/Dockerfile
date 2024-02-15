# v9.1.18
FROM squidfunk/mkdocs-material@sha256:62d36688f2a53f4f6ee11bace3a0fd17eed7f38fa127a8c58f4fee704054e3a6
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

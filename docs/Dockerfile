# v9.1.18
FROM squidfunk/mkdocs-material@sha256:98c9809e64d0b9b3a4cf0c4c77d99e9bf42f2aaa331decb7c4b48ad4df64e6f5
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

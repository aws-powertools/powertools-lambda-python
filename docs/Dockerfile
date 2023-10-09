# v9.1.18
FROM squidfunk/mkdocs-material@sha256:a4cfa88f5db3f6cdc9d97966d60a1003b19c351c603e966500cf30053193ea97
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

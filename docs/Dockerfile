# v9.1.18
FROM squidfunk/mkdocs-material@sha256:c62453b1ba229982c6325a71165c1a3007c11bd3dd470e7a1446c5783bd145b4
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

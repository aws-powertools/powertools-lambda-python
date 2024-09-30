# v9.1.18
FROM squidfunk/mkdocs-material@sha256:8e8b333257d2a5866a5b20809440eec360cbe6a54dbee70aaacd45e95fc06cbb
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

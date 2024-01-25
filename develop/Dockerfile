# v9.1.18
FROM squidfunk/mkdocs-material@sha256:9aad7af2f62950826f57928e984ea8aa77a561f67b7f5fc251ced67d52a2a5fe
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

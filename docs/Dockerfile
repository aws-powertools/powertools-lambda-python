# v9.1.18
FROM squidfunk/mkdocs-material@sha256:58dee36ad85b0ae4836522ee6d3f0150d828bca9a1f7d3bfbf430bca771c1441
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

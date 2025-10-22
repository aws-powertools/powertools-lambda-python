# v9.1.18
FROM squidfunk/mkdocs-material@sha256:f5c556a6d30ce0c1c0df10e3c38c79bbcafdaea4b1c1be366809d0d4f6f9d57f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

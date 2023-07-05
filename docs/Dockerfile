# v9.1.18
FROM squidfunk/mkdocs-material@sha256:a28ed811514d6c6cf15a4bcf7a2ce21d03fcb5c8cbdc4e1fec8ba179ef58fbb5
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

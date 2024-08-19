# v9.1.18
FROM squidfunk/mkdocs-material@sha256:a73e4bbbccb09e5374cef28ebe68511c166222274f8486b25ad467ec1f5e8bbe
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

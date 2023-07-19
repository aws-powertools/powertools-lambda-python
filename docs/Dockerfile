# v9.1.18
FROM squidfunk/mkdocs-material@sha256:33e28bdae302bc1aa9c6783dd863742416cb1174bae4ad9d7bcc5b2efe685639
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

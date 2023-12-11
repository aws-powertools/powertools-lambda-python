# v9.1.18
FROM squidfunk/mkdocs-material@sha256:876b39cd990973a8cc421ef7321d0b000289db9cb9b19d9df9186e4f6f705996
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

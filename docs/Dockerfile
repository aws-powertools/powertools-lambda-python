# v9.1.18
FROM squidfunk/mkdocs-material@sha256:6c81a890d0b5a59cc36e53684ae696995aa1f526f1406106f9bfec49d5031581
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

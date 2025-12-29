# v9.1.18
FROM squidfunk/mkdocs-material@sha256:3bba0a99bc6e635bb8e53f379d32ab9cecb554adee9cc8f59a347f93ecf82f3b
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

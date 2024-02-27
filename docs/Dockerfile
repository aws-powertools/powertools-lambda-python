# v9.1.18
FROM squidfunk/mkdocs-material@sha256:43b898a5520bbe5ee0080568c002491cd8fcd2269e64f7ad2ba4c9c419acb866
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

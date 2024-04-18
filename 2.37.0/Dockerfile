# v9.1.18
FROM squidfunk/mkdocs-material@sha256:521644b58bc0c806083ef66e8b1027861bd3e98c433b251c436c5c0cc7733603
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

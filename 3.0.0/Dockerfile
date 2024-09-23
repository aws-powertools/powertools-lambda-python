# v9.1.18
FROM squidfunk/mkdocs-material@sha256:a2e3a31c00cfe1dd2dae83ba21dbfa2c04aee2fa2414275c230c27b91a4eda09
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

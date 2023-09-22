# v9.1.18
FROM squidfunk/mkdocs-material@sha256:b41ba6dba2047d995bb89bf5a9a01e7eca05d2d8bd34d42028fa85399c825766
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

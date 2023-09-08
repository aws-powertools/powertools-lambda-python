# v9.1.18
FROM squidfunk/mkdocs-material@sha256:dd1770cc7bcb103d9fd3618006c66aaf6c0c829e23974ec0c0a3700558c553a1
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

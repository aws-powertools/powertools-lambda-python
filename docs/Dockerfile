# v9.1.18
FROM squidfunk/mkdocs-material@sha256:2a703999163cdb8257a85849fb2d39914a82587769f95c297bb3f01acf72a609
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

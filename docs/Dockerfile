# v9.1.18
FROM squidfunk/mkdocs-material@sha256:047452c6641137c9caa3647d050ddb7fa67b59ed48cc67ec3a4995f3d360ab32
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

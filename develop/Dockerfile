# v9.1.18
FROM squidfunk/mkdocs-material@sha256:20241c68151b5c46581335dfafe786e50d1e107f9bd9ecb639ed46627f32a31f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

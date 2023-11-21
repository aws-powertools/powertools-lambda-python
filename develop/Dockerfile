# v9.1.18
FROM squidfunk/mkdocs-material@sha256:fc42bac0005e79c2b2dd576e72103b06932c30c7b7b455a1f9cd3d39b187d49d
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

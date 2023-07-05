# v9.1.18
FROM squidfunk/mkdocs-material@sha256:3837c0f327033a6946a2810760fe80ee1f02fceda4f817638ea69c612b2db837
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

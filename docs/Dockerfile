# v9.1.18
FROM squidfunk/mkdocs-material@sha256:209b62dd9530163cc5cf9a49853b5bb8570ffb3f3b5fe4eadc1d319bbda5ce2f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

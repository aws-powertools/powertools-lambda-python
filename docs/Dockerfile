# v9.1.18
FROM squidfunk/mkdocs-material@sha256:86d21da4f45f16e30774bf911e5b4795da13ce0cd197dbf8d3d059f256b2cc37
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

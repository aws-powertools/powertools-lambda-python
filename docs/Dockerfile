# v9.1.18
FROM squidfunk/mkdocs-material@sha256:f226a2d2d5983643cab401491fc40e8a5711a50e90c21433f80e91c014cff1f5
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

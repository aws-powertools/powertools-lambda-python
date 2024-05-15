# v9.1.18
FROM squidfunk/mkdocs-material@sha256:8ef47d7116605e6b09860263af7278461c8dfca5dd3995f823dc96ea98b3f06c
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

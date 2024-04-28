# v9.1.18
FROM squidfunk/mkdocs-material@sha256:e3090898189e428f51f46faa2a59c90765abf8304fe4d2d2c401199d170cd991
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

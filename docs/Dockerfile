# v9.1.18
FROM squidfunk/mkdocs-material@sha256:6a72238e24c73e4cebb1ceddf8603778d25739ffbf480a314628a3d81aee2214
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

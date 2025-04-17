# v9.1.18
FROM squidfunk/mkdocs-material@sha256:95f2ff42251979c043d6cb5b1c82e6ae8189e57e02105813dd1ce124021a418b
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

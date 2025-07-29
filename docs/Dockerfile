# v9.1.18
FROM squidfunk/mkdocs-material@sha256:bb7b015690d9fb5ef0dbc98ca3520f153aa43129fb96aec5ca54c9154dc3b729
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

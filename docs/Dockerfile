# v9.1.18
FROM squidfunk/mkdocs-material@sha256:9835a76b0752159515e508e5e6ea4e7a41fc6630b797e31642d4bb32dc2f4032
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

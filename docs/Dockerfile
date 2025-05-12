# v9.1.18
FROM squidfunk/mkdocs-material@sha256:f6c81d538499f5755c8d1486f0abcda50bb631be391890ef823fcba18803114a
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

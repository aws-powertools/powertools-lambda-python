# v9.1.18
FROM squidfunk/mkdocs-material@sha256:772e14ebc0f53435e682c8dbb5ab47b3862a37dfd2c465514602f25bcf52173e
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

# v9.1.18
FROM squidfunk/mkdocs-material@sha256:2f29d716a52a50607ffbccd05463f511ed02f7492ebd9ae3a7bfb0ae83078ac2
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

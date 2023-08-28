# v9.1.18
FROM squidfunk/mkdocs-material@sha256:b1f7f94cf0e31dc40eb505c5f49bbcf42821d6e1ef409c52aafeff827ecb69b7
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

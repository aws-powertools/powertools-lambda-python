# v9.1.18
FROM squidfunk/mkdocs-material@sha256:f4764d119e53cc12b738bafb2534a91f992bf1d7e567098f980712a0ddd35ef4
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

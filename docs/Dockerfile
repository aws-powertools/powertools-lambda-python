# v9.1.18
FROM squidfunk/mkdocs-material@sha256:a4a2029fdf524f0c727852e492cd2bbae30cc9471959da60d7dc46bf565a521b
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

# v9.1.18
FROM squidfunk/mkdocs-material@sha256:e0d6c671fa3d5cf332043a5231c6f0cd68f48607e9edf710c2f3a57a74dbdc93
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

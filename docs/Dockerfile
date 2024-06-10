# v9.1.18
FROM squidfunk/mkdocs-material@sha256:96abcbb1bb6d4d79a6a142fe88150b3862b2b297fe45e6656b154d978b1787eb
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

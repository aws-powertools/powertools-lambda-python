# v9.1.18
FROM squidfunk/mkdocs-material@sha256:4ff781ee08fe02468f18ac85d5345956b41e1267c3269ccea8c2775c5eca161f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

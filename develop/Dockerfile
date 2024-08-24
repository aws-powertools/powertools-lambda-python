# v9.1.18
FROM squidfunk/mkdocs-material@sha256:7132ca3957c1fc325443579356fcc68696cd1aa54c715ce61228ea5e0b2d427a
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

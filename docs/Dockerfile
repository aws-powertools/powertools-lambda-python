# v9.1.18
FROM squidfunk/mkdocs-material@sha256:5358893a04dc6ed0e267ef1c0c06abc5d6b00d13dd0fee703c978ef98d56fd53
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

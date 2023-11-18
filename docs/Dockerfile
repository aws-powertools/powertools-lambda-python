# v9.1.18
FROM squidfunk/mkdocs-material@sha256:2c57e4d0fe6ad69e38e1198a59871638256ab9fdeab74f0fe79b42d6b380a23f
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

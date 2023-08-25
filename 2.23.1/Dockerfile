# v9.1.18
FROM squidfunk/mkdocs-material@sha256:97da15bac17e76561c88c87d5734583fd2d638a51c9f28a1a7ba8e8aa34c0fc9
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

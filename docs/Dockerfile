# v9.1.18
FROM squidfunk/mkdocs-material@sha256:31eb7f7c86dc35e29ca5520e1826b3c7fd54ddd84adc20cb0a42f59d17aa912e
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

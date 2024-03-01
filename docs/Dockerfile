# v9.1.18
FROM squidfunk/mkdocs-material@sha256:7be068b884750631488cd29cff0101a234971dfd7473276d050736b1cd1dac35
# pip-compile --generate-hashes --output-file=requirements.txt requirements.in
COPY requirements.txt /tmp/
RUN pip install --require-hashes -r /tmp/requirements.txt

FROM gcr.io/oss-fuzz-base/base-builder-python

# Copy project source
COPY . $SRC/powertools

WORKDIR $SRC/powertools

# Install project dependencies
RUN pip3 install -e ".[all]"

# Copy build script
COPY .clusterfuzzlite/build.sh $SRC/

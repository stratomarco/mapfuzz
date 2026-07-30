FROM gcr.io/oss-fuzz-base/base-builder
RUN apt-get update && apt-get install -y cmake ninja-build zip
COPY . $SRC/mapfuzz
WORKDIR $SRC/mapfuzz
COPY oss-fuzz/build.sh $SRC/build.sh

#!/bin/bash -eu
# OSS-Fuzz / ClusterFuzzLite build script for the mapfuzz GGUF target.
# The base-builder image provides $CC $CXX $CFLAGS $CXXFLAGS (with the selected
# sanitizer + coverage) and $LIB_FUZZING_ENGINE. We build ggml with those flags
# so the whole loader is instrumented, then link the harness with the engine.

LLAMA_COMMIT="${LLAMA_COMMIT:-432d7ffe2c3b4e539f3d0d4ae0a4893090a018d6}"

git clone https://github.com/ggml-org/llama.cpp.git "$SRC/llama.cpp"
git -C "$SRC/llama.cpp" fetch --depth 1 origin "$LLAMA_COMMIT"
git -C "$SRC/llama.cpp" checkout -q "$LLAMA_COMMIT"

cmake -S "$SRC/llama.cpp" -B "$WORK/ggml-build" -G Ninja \
    -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
    -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DGGML_BACKEND_DL=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TOOLS=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_COMMON=OFF \
    -DCMAKE_C_FLAGS="$CFLAGS" -DCMAKE_CXX_FLAGS="$CXXFLAGS"
ninja -C "$WORK/ggml-build" ggml ggml-base ggml-cpu

GB="$WORK/ggml-build/ggml/src"
$CXX $CXXFLAGS -std=c++17 \
    -I "$SRC/llama.cpp/ggml/include" \
    "$SRC/mapfuzz/targets/gguf/harness/gguf_fuzz_harness.cpp" \
    $LIB_FUZZING_ENGINE \
    -Wl,--start-group "$GB/libggml.a" "$GB/libggml-cpu.a" "$GB/libggml-base.a" -Wl,--end-group \
    -lpthread -ldl -lm \
    -o "$OUT/fuzz_gguf"

# seed corpus
mkdir -p "$OUT/fuzz_gguf_seed_corpus"
cp "$SRC/mapfuzz/targets/gguf/corpus/"* "$OUT/fuzz_gguf_seed_corpus/" || true
( cd "$OUT/fuzz_gguf_seed_corpus" && zip -q -r "$OUT/fuzz_gguf_seed_corpus.zip" . ) || true

#!/usr/bin/env bash
#
# Reproducible build for the GGUF parser fuzz harness.
# Clones llama.cpp at a pinned commit, builds ggml as an instrumented static
# library (coverage + AddressSanitizer), and links the libFuzzer harness.
#
# API and crash locations in this target were verified against this exact commit.
# Bumping the pin requires re-verifying the entry point in harness/ and the
# findings in PRIVATE_findings/.

set -euo pipefail

# --- configuration ---------------------------------------------------------
LLAMA_REPO="${LLAMA_REPO:-https://github.com/ggml-org/llama.cpp.git}"
LLAMA_COMMIT="${LLAMA_COMMIT:-432d7ffe2c3b4e539f3d0d4ae0a4893090a018d6}"  # ggml 0.18.0, 2026-07-30
CC="${CC:-clang}"
CXX="${CXX:-clang++}"

# Sanitizer / coverage flags. Add ',undefined' to hunt the integer-overflow and
# type-confusion classes; kept to address + coverage here for a clean happy path.
SAN="${SAN:--fsanitize=fuzzer-no-link,address -fno-omit-frame-pointer -g -O1}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${WORK:-$HERE/.build}"
SRC="$WORK/llama.cpp"
GGML_BUILD="$WORK/ggml-build"

# --- fetch upstream at the pinned commit -----------------------------------
mkdir -p "$WORK"
if [ ! -d "$SRC/.git" ]; then
    git clone "$LLAMA_REPO" "$SRC"
fi
git -C "$SRC" fetch --depth 1 origin "$LLAMA_COMMIT"
git -C "$SRC" checkout -q "$LLAMA_COMMIT"

# --- build instrumented ggml static libs (CPU only) ------------------------
cmake -S "$SRC" -B "$GGML_BUILD" -G Ninja \
    -DCMAKE_C_COMPILER="$CC" -DCMAKE_CXX_COMPILER="$CXX" \
    -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DGGML_BACKEND_DL=OFF \
    -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TOOLS=OFF -DLLAMA_BUILD_SERVER=OFF -DLLAMA_BUILD_COMMON=OFF \
    -DCMAKE_C_FLAGS="$SAN" -DCMAKE_CXX_FLAGS="$SAN"
ninja -C "$GGML_BUILD" ggml ggml-base ggml-cpu

# --- link the harness with the libFuzzer driver ----------------------------
GB="$GGML_BUILD/ggml/src"
"$CXX" -std=c++17 -fsanitize=fuzzer,address -fno-omit-frame-pointer -g -O1 \
    -I "$SRC/ggml/include" \
    "$HERE/harness/gguf_fuzz_harness.cpp" \
    -Wl,--start-group "$GB/libggml.a" "$GB/libggml-cpu.a" "$GB/libggml-base.a" -Wl,--end-group \
    -lpthread -ldl -lm \
    -o "$HERE/fuzz_gguf"

echo "built: $HERE/fuzz_gguf"
echo "run:   $HERE/fuzz_gguf -max_total_time=60 $HERE/corpus/"

# 32-bit variant (REQ-N3): the alignment-overflow class from the 2026-05-15
# advisory only manifests on 32-bit. Not yet wired here; add a -m32 toolchain
# file and multilib runtime, then rebuild with the same flags.

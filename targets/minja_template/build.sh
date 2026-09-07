#!/usr/bin/env bash
# Build the minja harnesses (libFuzzer + ASan + UBSan). minja is header-only; we
# vendor its two headers into .deps/ at a pinned version. clang with libFuzzer
# required. Builds both fuzz_parse (parser) and fuzz_render (interpreter).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# Historical target: supplied pins must come from a reviewed reproduction record.
: "${MINJA_COMMIT:?Set the reviewed 40-character minja commit}"
: "${JSON_COMMIT:?Set the reviewed 40-character nlohmann/json commit}"
: "${MINJA_SHA256:?Set the reviewed minja.hpp sha256}"
: "${JSON_SHA256:?Set the reviewed json.hpp sha256}"
[[ "$MINJA_COMMIT" =~ ^[0-9a-f]{40}$ && "$JSON_COMMIT" =~ ^[0-9a-f]{40}$ ]] || exit 1
[[ "$MINJA_SHA256" =~ ^[0-9a-f]{64}$ && "$JSON_SHA256" =~ ^[0-9a-f]{64}$ ]] || exit 1
DEPS=".deps/$MINJA_COMMIT-$JSON_COMMIT"
mkdir -p "$DEPS/minja" "$DEPS/nlohmann"
curl -fsSL "https://raw.githubusercontent.com/google/minja/$MINJA_COMMIT/include/minja/minja.hpp" -o "$DEPS/minja/minja.hpp"
curl -fsSL "https://raw.githubusercontent.com/nlohmann/json/$JSON_COMMIT/single_include/nlohmann/json.hpp" -o "$DEPS/nlohmann/json.hpp"
echo "$MINJA_SHA256  $DEPS/minja/minja.hpp" | sha256sum -c -
echo "$JSON_SHA256  $DEPS/nlohmann/json.hpp" | sha256sum -c -
FLAGS="-std=c++17 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all -I$DEPS"
clang++ $FLAGS harness/fuzz_parse.cc -o fuzz_parse
# render: recover from div-by-zero so the campaign explores past that known bug
# (all other checks stay fatal). parse does no arithmetic so keeps strict flags.
clang++ $FLAGS -fsanitize-recover=integer-divide-by-zero,float-divide-by-zero harness/fuzz_render.cc -o fuzz_render
echo "built: fuzz_parse (parser), fuzz_render (interpreter)"
echo "run: ./fuzz_render -max_total_time=3600 -rss_limit_mb=4096 corpus/"

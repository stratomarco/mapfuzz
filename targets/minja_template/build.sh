#!/usr/bin/env bash
# Build the minja harnesses (libFuzzer + ASan + UBSan). minja is header-only; we
# vendor its two headers into .deps/ at a pinned version. clang with libFuzzer
# required. Builds both fuzz_parse (parser) and fuzz_render (interpreter).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
DEPS=.deps
mkdir -p "$DEPS/minja" "$DEPS/nlohmann"
[ -f "$DEPS/minja/minja.hpp" ] || curl -fsSL "https://raw.githubusercontent.com/google/minja/main/include/minja/minja.hpp" -o "$DEPS/minja/minja.hpp"
[ -f "$DEPS/nlohmann/json.hpp" ] || curl -fsSL "https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp" -o "$DEPS/nlohmann/json.hpp"
FLAGS="-std=c++17 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all -I$DEPS"
clang++ $FLAGS harness/fuzz_parse.cc  -o fuzz_parse
clang++ $FLAGS harness/fuzz_render.cc -o fuzz_render
echo "built: fuzz_parse (parser), fuzz_render (interpreter)"
echo "run: ./fuzz_render -max_total_time=3600 -rss_limit_mb=4096 corpus/"

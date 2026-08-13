#!/usr/bin/env bash
# Build the minja chat-template parse harness (libFuzzer + ASan + UBSan).
# minja is header-only; we vendor its two headers (minja.hpp + nlohmann/json.hpp)
# into .deps/ at a pinned version. clang with libFuzzer required.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
DEPS=.deps
mkdir -p "$DEPS/minja" "$DEPS/nlohmann"
if [ ! -f "$DEPS/minja/minja.hpp" ]; then
  curl -fsSL "https://raw.githubusercontent.com/google/minja/main/include/minja/minja.hpp" -o "$DEPS/minja/minja.hpp"
fi
if [ ! -f "$DEPS/nlohmann/json.hpp" ]; then
  curl -fsSL "https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp" -o "$DEPS/nlohmann/json.hpp"
fi
clang++ -std=c++17 -g -O1 -fsanitize=fuzzer,address,undefined -fno-sanitize-recover=all \
  -I"$DEPS" harness/fuzz_parse.cc -o fuzz_minja
echo "built: $(pwd)/fuzz_minja"
echo "run: ./fuzz_minja -max_total_time=600 corpus/"

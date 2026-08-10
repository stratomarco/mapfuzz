#!/usr/bin/env bash
#
# Reproducible cargo-fuzz build for the tokenizers from_bytes harness.
#
# cargo-fuzz requires a nightly toolchain for its sanitizer and coverage
# instrumentation. This script installs nightly and cargo-fuzz if missing,
# then builds the target. Requires rustup.
#
# Entry point (Tokenizer::from_bytes) was verified against source at the pinned
# crate version. Bumping the pin in fuzz/Cargo.toml requires re-verifying it.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if ! command -v rustup >/dev/null 2>&1; then
    echo "error: rustup not found. Install from https://rustup.rs then re-run." >&2
    exit 1
fi

# nightly is required by cargo-fuzz
rustup toolchain list | grep -q '^nightly' || rustup toolchain install nightly
# cargo-fuzz provides the build and run wrappers over libFuzzer
command -v cargo-fuzz >/dev/null 2>&1 || cargo install cargo-fuzz

echo "=== fuzz targets ==="
cargo +nightly fuzz list

echo "=== building from_bytes (ASan + coverage) ==="
cargo +nightly fuzz build from_bytes

echo
echo "built. run a campaign with:"
echo "  cargo +nightly fuzz run from_bytes -- -max_total_time=600 -rss_limit_mb=4096"
echo
echo "the seed corpus lives in corpus/; cargo-fuzz keeps its working corpus"
echo "under fuzz/corpus/from_bytes/. Seed it once with:"
echo "  mkdir -p fuzz/corpus/from_bytes && cp corpus/* fuzz/corpus/from_bytes/"
echo
echo "to widen the parse surface, enable more tokenizers features in"
echo "fuzz/Cargo.toml (onig needs libonig-dev; see README)."

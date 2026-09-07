#!/usr/bin/env bash
# Regression build; exact dated nightly and cargo-fuzz required, no global installs.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
: "${RUST_TOOLCHAIN:?Set an installed nightly-YYYY-MM-DD toolchain}"
[[ "$RUST_TOOLCHAIN" =~ ^nightly-[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || { echo 'dated nightly required' >&2; exit 1; }
: "${CARGO_FUZZ_VERSION:?Set the reviewed installed cargo-fuzz version}"
[[ "$(cargo fuzz --version)" = "cargo-fuzz $CARGO_FUZZ_VERSION" ]] || { echo 'cargo-fuzz version mismatch' >&2; exit 1; }
[[ -f fuzz/Cargo.lock ]] || { echo 'resolve and review fuzz/Cargo.lock before building' >&2; exit 1; }
rustc +"$RUST_TOOLCHAIN" --version
# cargo-fuzz 0.13.2 does not forward --locked. Validate/fetch the resolution
# first, build offline, then reject any lock drift.
cargo +"$RUST_TOOLCHAIN" metadata --locked --manifest-path fuzz/Cargo.toml --format-version 1 >/dev/null
lock_before=$(sha256sum fuzz/Cargo.lock)
CARGO_NET_OFFLINE=true cargo +"$RUST_TOOLCHAIN" fuzz build from_bytes
[[ "$(sha256sum fuzz/Cargo.lock)" = "$lock_before" ]] || { echo 'dependency lock changed during build' >&2; exit 1; }

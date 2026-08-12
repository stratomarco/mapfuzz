#!/usr/bin/env bash
# Corpus management for continuous fuzzing persistence.
#
# The point of "continuous" fuzzing is that coverage ACCUMULATES across runs. A
# run that starts from a cold seed re-discovers the same coverage every time and
# never gets deeper. This script wraps the persist/minimize cycle so a CI job can:
#
#   1. restore an accumulated corpus (from cache) into the working corpus dir
#   2. fuzz into that dir (the harness appends coverage-growing inputs)
#   3. minimize it (-merge=1) to a coverage-preserving minimal set before saving,
#      so the cached corpus does not bloat over time
#
# Usage:
#   corpus.sh minimize <fuzz_cmd> <dst_min_dir> <src_corpus_dir>
#   corpus.sh seed <corpus_dir> <seed_dir>     # copy seeds in if corpus empty
#
# <fuzz_cmd> is the harness invocation (e.g. "./fuzz_gguf" or
# "python3 harness/fuzz_x.py"). Works for libFuzzer and Atheris (both support
# -merge=1).
set -euo pipefail

cmd="${1:-}"; shift || true

case "$cmd" in
  seed)
    corpus_dir="${1:?corpus dir}"; seed_dir="${2:?seed dir}"
    mkdir -p "$corpus_dir"
    if [ -z "$(ls -A "$corpus_dir" 2>/dev/null)" ]; then
      cp "$seed_dir"/* "$corpus_dir"/ 2>/dev/null || true
      echo "corpus.sh: seeded $corpus_dir from $seed_dir"
    else
      echo "corpus.sh: $corpus_dir already has inputs; keeping accumulated corpus"
    fi
    ;;
  minimize)
    fuzz_cmd="${1:?fuzz cmd}"; dst="${2:?dst min dir}"; src="${3:?src corpus dir}"
    mkdir -p "$dst"
    # -merge=1 keeps only inputs that add coverage; dst becomes the minimal set.
    # Tolerate a merge that finds nothing (empty corpus) without failing the job.
    $fuzz_cmd -merge=1 "$dst" "$src" 2>&1 | tail -3 || true
    n_src=$(ls -A "$src" 2>/dev/null | wc -l)
    n_dst=$(ls -A "$dst" 2>/dev/null | wc -l)
    echo "corpus.sh: minimized $n_src -> $n_dst inputs (coverage-preserving)"
    ;;
  *)
    echo "usage: corpus.sh {seed <corpus_dir> <seed_dir> | minimize <fuzz_cmd> <dst> <src>}" >&2
    exit 2
    ;;
esac

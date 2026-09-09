#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
    echo "usage: $0 BUILD_DIR SEED CORPUS_DIR OUTPUT_DIR" >&2
    exit 2
fi

target_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=environment.env
source "${target_dir}/environment.env"
build_dir="$(realpath "$1")"
seed="$(realpath "$2")"
corpus_dir="$(realpath "$3")"
output_dir="$4"
fuzzer="${build_dir}/fuzz-clip-materialize"

test -x "${fuzzer}"
test -f "${seed}"
test -d "${corpus_dir}"
test -f "${corpus_dir}/benign.gguf"
cmp -s "${seed}" "${corpus_dir}/benign.gguf"
test ! -e "${output_dir}"

echo "seed_sha256=$(sha256sum "${seed}" | cut -d " " -f 1)"

systemd-run --user --scope --collect \
    -p MemoryMax=4294967296 \
    -p MemorySwapMax=0 \
    taskset -c 0 python3 "${target_dir}/qualification/cgroup_exec.py" \
    python3 -m chassis.campaign \
    --output "${output_dir}" \
    --timeout 90 \
    -- setarch "${SETARCH_MACHINE}" -R "${fuzzer}" \
    -max_total_time=60 \
    -timeout=5 \
    -rss_limit_mb=4096 \
    "${corpus_dir}"

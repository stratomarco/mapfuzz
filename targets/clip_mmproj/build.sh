#!/usr/bin/env bash
set -euo pipefail

target_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${target_dir}/../.." && pwd)"

# shellcheck source=environment.env
source "${target_dir}/environment.env"

test "$(ninja --version)" = "${NINJA_VERSION}"
cmake --version | head -n 1 | grep -Fqx "cmake version ${CMAKE_VERSION}"
"${CC}" --version | head -n 1 | grep -F "clang version ${CLANG_VERSION}"
python3 --version | grep -Fqx "Python ${PYTHON_PRIMARY_VERSION}"
test "$(uname -m)" = "${SETARCH_MACHINE}"
command -v setarch >/dev/null

work_root="${CLIP_MM_PROJ_WORK_ROOT:-${repo_root}/.runs/clip-mmproj-build}"
source_dir="${work_root}/llama.cpp"
build_dir="${work_root}/build"

if [[ -e "${source_dir}" || -e "${build_dir}" ]]; then
    echo "refusing to reuse source/build state: ${work_root}" >&2
    echo "select a fresh CLIP_MM_PROJ_WORK_ROOT" >&2
    exit 2
fi

mkdir -p "${work_root}"
git init "${source_dir}"
git -C "${source_dir}" remote add origin https://github.com/ggml-org/llama.cpp.git
git -C "${source_dir}" fetch --depth 1 origin "${LLAMA_CPP_REVISION}"
git -C "${source_dir}" checkout --detach FETCH_HEAD
test "$(git -C "${source_dir}" rev-parse HEAD)" = "${LLAMA_CPP_REVISION}"

known_blockers_patch="${target_dir}/fuzz-blockers/clip-type-and-nlayer-fix.patch"
bad_alloc_patch="${target_dir}/qualification/patches/rethrow-bad-alloc.patch"
mlp_layout_patch="${target_dir}/qualification/patches/validate-mlp-layout.patch"
git -C "${source_dir}" apply --check "${known_blockers_patch}"
git -C "${source_dir}" apply "${known_blockers_patch}"
git -C "${source_dir}" apply --check "${bad_alloc_patch}"
git -C "${source_dir}" apply "${bad_alloc_patch}"
git -C "${source_dir}" apply --check "${mlp_layout_patch}"
git -C "${source_dir}" apply "${mlp_layout_patch}"
sha256sum "${known_blockers_patch}" "${bad_alloc_patch}" "${mlp_layout_patch}"
git -C "${source_dir}" diff --check

echo "ninja_version=${NINJA_VERSION}"
echo "clang_version=${CLANG_VERSION}"
echo "cmake_version=${CMAKE_VERSION}"
echo "python_version=${PYTHON_PRIMARY_VERSION}"
echo "asan_replay_wrapper=setarch ${SETARCH_MACHINE} -R"

cmake -S "${target_dir}/qualification" -B "${build_dir}" \
    -G "${CMAKE_GENERATOR}" \
    -DCMAKE_BUILD_TYPE="${CMAKE_BUILD_TYPE}" \
    -DCMAKE_C_COMPILER="${CC}" \
    -DCMAKE_CXX_COMPILER="${CXX}" \
    -DLLAMA_SOURCE_DIR="${source_dir}"
cmake --build "${build_dir}" --parallel "${MAX_BUILD_JOBS}"

sha256sum \
    "${build_dir}/clip-mmproj-seed" \
    "${build_dir}/clip-mmproj-qualify" \
    "${build_dir}/fuzz-clip-materialize"

echo "build_dir=${build_dir}"
echo "source_revision=$(git -C "${source_dir}" rev-parse HEAD)"
echo "source_worktree_patches=known-blockers,rethrow-bad-alloc,validate-mlp-layout"

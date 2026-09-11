#!/usr/bin/env bash
set -euo pipefail

readonly UPSTREAM_SHA="b6ec0060779550c0a157ae34feb89e0cf86012a8"
readonly ARCHIVE_SHA="429a869b02b3fd8b9745f390951148f5185fce42d7bd7678337981d4510324d7"
readonly PYPROJECT_SHA="d67a60c007eeb4401b29818d99a6ad94aa28c1f10beabdcf77c4da5d97f8e326"
readonly LOCK_SHA="4a56d47d2edfdc159bd137c854d37033028f38c4d9d57ec98284d8fce9ea2ccc"
readonly UV_VERSION="0.11.30"
readonly UV_BIN_SHA="9a4299a0c3bcc01012acbcdae7b5655e5087e0e5d87459306736a1420a902b81"

repo_root="$(git rev-parse --show-toplevel)"
run_root="${1:-${repo_root}/.runs/lerobot-r8-bootstrap}"

if [[ -e "${run_root}" ]]; then
  echo "refusing to reuse existing run root: ${run_root}" >&2
  exit 2
fi

mkdir -p "${run_root}/source"
curl --fail --location --proto '=https' --tlsv1.2 \
  "https://github.com/huggingface/lerobot/archive/${UPSTREAM_SHA}.tar.gz" \
  --output "${run_root}/source.tar.gz"
echo "${ARCHIVE_SHA}  ${run_root}/source.tar.gz" | sha256sum --check --status
tar -xzf "${run_root}/source.tar.gz" --strip-components=1 -C "${run_root}/source"
echo "${PYPROJECT_SHA}  ${run_root}/source/pyproject.toml" | sha256sum --check --status
echo "${LOCK_SHA}  ${run_root}/source/uv.lock" | sha256sum --check --status

python3.12 -m venv "${run_root}/uv-bootstrap"
"${run_root}/uv-bootstrap/bin/python" -m pip install \
  --disable-pip-version-check "uv==${UV_VERSION}"
[[ "$("${run_root}/uv-bootstrap/bin/uv" --version)" == "uv ${UV_VERSION} (x86_64-unknown-linux-gnu)" ]]
echo "${UV_BIN_SHA}  ${run_root}/uv-bootstrap/bin/uv" | sha256sum --check --status

(
  cd "${run_root}/source"
  env \
    UV_PROJECT_ENVIRONMENT="${run_root}/env" \
    UV_CACHE_DIR="${run_root}/uv-cache" \
    "${run_root}/uv-bootstrap/bin/uv" sync \
      --locked --extra dataset --extra test --no-dev
)

env CUDA_VISIBLE_DEVICES='' "${run_root}/env/bin/python" - <<'PY' > "${run_root}/decoder.txt"
import av
import torch

expected = {
    "libavcodec": (61, 19, 101),
    "libavformat": (61, 7, 100),
    "libavutil": (59, 39, 100),
    "libswscale": (8, 3, 100),
}
assert av.__version__ == "15.1.0"
for library, version in expected.items():
    assert av.library_versions[library] == version
assert av.codec.Codec("libx264", "w").name == "libx264"
assert not torch.cuda.is_available()
print(f"av={av.__version__}")
for library in sorted(av.library_versions):
    print(f"{library}={'.'.join(map(str, av.library_versions[library]))}")
print("encoder=libx264")
print("cuda_available=false")
PY

"${run_root}/env/bin/python" --version > "${run_root}/python-version.txt"
"${run_root}/uv-bootstrap/bin/uv" --version > "${run_root}/uv-version.txt"
"${run_root}/uv-bootstrap/bin/uv" pip freeze \
  --python "${run_root}/env/bin/python" | LC_ALL=C sort > "${run_root}/packages.txt"
uname -a > "${run_root}/system.txt"
sha256sum \
  "${run_root}/source.tar.gz" \
  "${run_root}/source/pyproject.toml" \
  "${run_root}/source/uv.lock" \
  "${run_root}/decoder.txt" \
  "${run_root}/packages.txt" \
  "${run_root}/python-version.txt" \
  "${run_root}/uv-version.txt" \
  "${run_root}/system.txt" > "${run_root}/environment.sha256"

printf 'environment=%s\npython=%s\n' "${run_root}" "${run_root}/env/bin/python"

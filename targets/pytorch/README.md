# Target: PyTorch weights_only restricted unpickler

## Loader under test

- Format: PyTorch checkpoint (`.pt` / `.pth`), a zip archive containing a pickle
  stream (`data.pkl`) plus tensor storage. This target fuzzes the pickle-stream
  layer directly.
- Implementation: `torch._weights_only_unpickler`.
- Entry point: `torch._weights_only_unpickler.load(file)` (verified at line 592
  of `torch/_weights_only_unpickler.py` on `main`).
- Version under test: pin the CURRENT release in `build.sh` (`TORCH_SPEC`).

The harness feeds bytes straight to the restricted unpickler rather than through
`torch.load`, so mutations land directly in the opcode dispatch, which is where
the recent bugs live. A separate harness can target the full `torch.load`
zip-container path.

## Scope and intent (important)

This target hunts CRASHES and unexpected failures in the RESTRICTED unpickler,
the path `torch.load(..., weights_only=True)` uses and that is explicitly meant
to be safe against untrusted checkpoints. That "raw pickle executes code" is not
a finding; it is documented and by design. The productive, current frontier is
malformed opcode streams and malformed reduce/storage arguments reaching the
tensor backend through allowlisted functions, the class of CVE-2026-24747.

This is defect demonstration, not weaponization. The harness never builds a
working RCE payload. A finding is a crash, an unexpected failure, or a minimal
reproducer showing the restricted loader reached something it should not, all
for coordinated disclosure. Building a deployable malicious model is out of
scope and not done here.

## M0 audit result

- `pytorch` is not an OSS-Fuzz project (`projects/pytorch/project.yaml` returns
  404; `sentencepiece` control returns 200). The restricted unpickler is not
  under continuous public fuzzing.
- The area is active, not quiet: CVE-2025-32434 (legacy `.tar` path bypass,
  fixed 2.6.0) and CVE-2026-24747 (opcode/metadata memory corruption in the
  weights_only unpickler, fixed 2.10.0). We target the current release, where
  those fixes are present (verified: `_check_set_item_target` guards the
  SETITEM/SETITEMS path, BUILD is restricted to Tensor/Parameter/OrderedDict,
  APPEND/APPENDS restricted to lists), so we hunt the next gap, not a known bug.
- Conclusion: high-value, active, not continuously fuzzed. Expect competition
  from other researchers; the freshly-hardened guard code is the place to look.

## Bug classes targeted

- Opcode-VM faults: stack underflow and index errors in handlers that index
  `self.stack[-1]` (including the new guard functions), reachable via crafted
  opcode sequences.
- Allowlisted-global, untrusted-argument crashes: `REDUCE` calls
  `func(*args)` and `BUILD` calls `inst.set_(*state)` / `__setstate__(state)`
  with attacker-controlled arguments. The allowlist gates the function, not its
  arguments, so malformed arguments can reach the C++ tensor/storage backend and
  crash it. This is the CVE-2026-24747 class.
- Resource exhaustion: deep nesting (RecursionError), pathological counts.
- Safelist-escape signals (high value, harder to oracle automatically): the
  restricted loader constructing or invoking something outside its intended set.

## Seed corpus

`corpus/seed_state_dict.pkl` is a builtin-only pickle (nested dicts and lists),
valid for the restricted unpickler, generated without torch. `build.sh`
additionally extracts a realistic tensor `data.pkl` from a saved state_dict on
the target machine, which gives the fuzzer real reduce/storage opcodes to
mutate. Seeds contain no proprietary weights.

## Build and run

Python + pip. Installs torch and atheris.

```
./build.sh
# blind harness (baseline; exhausts the shallow layer quickly):
python3 harness/fuzz_weights_only.py -max_total_time=600 -rss_limit_mb=4096 corpus/
# structure-aware generator (the productive one; reaches the tensor backend):
python3 harness/fuzz_rebuild_args.py -max_total_time=600 -rss_limit_mb=4096
# coverage-guided STABLE generator (fixed-layout decode; libFuzzer steers structure):
python3 harness/fuzz_rebuild_args_stable.py --selftest
python3 harness/fuzz_rebuild_args_stable.py -max_total_time=600 -rss_limit_mb=4096
# storage-backed OOB (probe first, then campaign):
python3 harness/fuzz_storage_oob.py --selftest
python3 harness/fuzz_storage_oob.py -max_total_time=600 -rss_limit_mb=4096
# container path: declared-vs-actual storage size mismatch (probe first):
python3 harness/fuzz_storage_mismatch.py --selftest
python3 harness/fuzz_storage_mismatch.py -max_total_time=600 -rss_limit_mb=4096
```

Four harnesses, increasing depth. `fuzz_weights_only` mutates raw bytes (opcode
parser; blind baseline found nothing in 6M runs). `fuzz_rebuild_args` generates
valid calls to `_rebuild_meta_tensor_no_storage` and fuzzes size/stride, reaching
`empty_strided` (verified reaching the backend by coverage growth; clean in 13M
runs, but the meta path has no real buffer). `fuzz_storage_oob` supplies a small
Python storage and fuzzes size/stride/offset to `_rebuild_tensor_v2`; it is
neutralized because torch RESIZES the Python storage to fit, so it cannot create
a real OOB (a documented negative result). `fuzz_storage_mismatch` is the answer
to that: it mutates a storage record's physical length inside a real checkpoint
zip so the declared nbytes disagrees with the actual record, reaching
`get_storage_from_record` in C++, which cannot resize a short record. That is the
CVE-2026-24747 surface. Always run `--selftest` first; for the container harness
the self-test also proves the repackaged zip is torch-readable, so a
wholesale-rejected input never produces a false-clean campaign.

## Status

Scaffold complete; entry point and current-release hardening verified against
source; harness syntax-validated and builtin seed generated. Full build-and-run
validation is pending on a machine with torch installed (the authoring sandbox
lacked disk for the ~2 GB package). First real campaign runs there.

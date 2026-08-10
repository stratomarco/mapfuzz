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
python3 harness/fuzz_weights_only.py -max_total_time=600 -rss_limit_mb=4096 corpus/
```

## Status

Scaffold complete; entry point and current-release hardening verified against
source; harness syntax-validated and builtin seed generated. Full build-and-run
validation is pending on a machine with torch installed (the authoring sandbox
lacked disk for the ~2 GB package). First real campaign runs there.

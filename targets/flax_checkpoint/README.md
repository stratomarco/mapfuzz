# Target: flax / JAX checkpoint restore

The JAX-ecosystem sibling of the pytorch weights_only target. Restoring an
untrusted JAX/flax checkpoint is a download-to-load trust boundary used by
DreamerV3 and most JAX world models.

## Loader under test

- Entry point: `flax.serialization.msgpack_restore(bytes) -> pytree` (verified,
  flax 0.12.8). flax serializes a pytree to msgpack with custom extension types;
  restore runs flax's own `_msgpack_ext_unpack` and `_ndarray_from_bytes`, which
  does `np.frombuffer(buffer, dtype=_dtype_from_name(dtype_name)).reshape(shape)`
  on an untrusted (shape, dtype_name, buffer) triple.
- Higher layer (next harness): `from_bytes` -> `from_state_dict`, flax's own
  structural matching of the restored tree against a target template (recursion,
  type/shape reconciliation) - richer coverage than the array path.

## M0

flax, orbax, jax, msgpack all NOT in OSS-Fuzz (pyyaml/sentencepiece are, so the
raw parse layers are covered; the JAX checkpoint-restore path is not). Open ground.

## Scope

Robustness/DoS on load (crashes, hangs, unhandled exceptions, unbounded
allocation). numpy blocks object-dtype arrays from buffers, so this is not a
code-execution surface. Defect demonstration only.

## Build and run

```
./build.sh
python3 harness/fuzz_msgpack_restore.py --selftest
python3 harness/fuzz_msgpack_restore.py -max_total_time=600 -rss_limit_mb=4096
```

## Status

Built and validated in-sandbox against flax 0.12.8. Self-test passes (round-trip
OK; generator 166/200 restored, 34 cleanly rejected). A ~480k-run campaign found
no crash: the array-reconstruction path is robust (numpy frombuffer/reshape
defenses hold; malformed shape/dtype/buffer reject cleanly). Coverage was flat
(cov 33), the array work is in numpy C code with weak coverage signal, so this is
a somewhat shallow negative. The `from_state_dict` structural-matching layer
(flax's own Python, richer coverage) is the more promising next harness.

## Second harness: fuzz_from_state_dict.py (structural layer)

Fuzzes flax.serialization.from_state_dict(target, state), the structural
reconciliation of an untrusted state against a target template. Richer coverage
than the array path (flax's own Python recursion, not numpy C code).

Result: one low-severity ROBUSTNESS observation, NOT a security finding. When the
state's type does not match the target (e.g. a non-dict where a dict is expected),
flax calls .keys() without a type check and raises a raw AttributeError
("'X' object has no attribute 'keys'") instead of its own SerializationError /
ValueError. All ~147 initially-flagged cases dedup to this SINGLE root cause
(different input types, same code path). Across 200k additional inputs filtering
this soft-spot, no other fault appeared: no recursion, no crash.

Assessment: this is a code-quality gap (wrong exception type / less helpful
message), not a vulnerability. The program does not crash and a caller's exception
handler still catches it. Distinct from 0002/0003, which were process-aborting
panics. Worth at most a small upstream PR adding a type check; NOT filed as a
security finding. Recorded here for completeness and to avoid re-discovering it.

The from_state_dict reconciliation logic is otherwise robust.

# Target: GGUF

## Loader under test

- Format: GGUF (the binary serialization format used to distribute quantized model weights).
- Implementation: ggml / llama.cpp.
- Entry point: `gguf_init_from_buffer(const void *data, size_t size, struct gguf_init_params params)`.
- Pinned commit: `432d7ffe2c3b4e539f3d0d4ae0a4893090a018d6` (ggml 0.18.0, 2026-07-30).

The entry point and the `gguf_init_params` struct (`{ bool no_alloc; struct ggml_context **ctx; }`) were read from `ggml/include/gguf.h` at the pinned commit, not assumed. If the pin is bumped, re-verify both before trusting the harness.

The harness uses the in-memory buffer entry point so no filesystem access happens per input, and sets `no_alloc = true` so it parses metadata and tensor descriptors without allocating tensor data. This reaches the alignment, offset, enum, and size-computation paths while keeping each run fast and bounded. All value accessors are gated on the type the loader reports, so the harness never invokes a type-mismatched accessor.

## Bug classes targeted

- Integer overflow and underflow in size, offset, alignment, and element-count math.
- Division by zero in size and element-count computation.
- Type confusion from enum and tag values deserialized without a bounds check.
- Out-of-bounds read and write, driven by attacker-controlled counts, lengths, and offsets.
- Resource exhaustion from attacker-scaled string, array, and tensor declarations.

## Triage note

Accessors can reach `GGML_ASSERT`, which calls `abort()` and appears to the fuzzer as a crash. Assertion-triggered aborts are a distinct triage category from memory-safety findings; classify them separately before reporting. Memory-safety findings are those where a sanitizer reports a read, write, overflow, or arithmetic fault, or where the fault occurs inside the parse routine rather than at an assertion.

## Seed corpus

`corpus/seed_minimal.gguf` is a minimal structurally valid file (a few typed key/value pairs and one small synthetic tensor), generated with the official `gguf` Python writer. It contains no proprietary weights.

## Build and run

```
./build.sh
./fuzz_gguf -max_total_time=60 -rss_limit_mb=2048 corpus/
```

Enable the integer and type-confusion oracles by adding `,undefined` to `SAN` in `build.sh`.

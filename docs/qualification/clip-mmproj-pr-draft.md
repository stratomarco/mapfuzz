# Local draft: validate complete CLIP MLP projector layouts

Status: local review artifact only. This is not an opened pull request, security
advisory, novelty claim, or authorization to contact upstream.

## Proposed title

`mtmd: validate complete MLP projector layouts before loading`

## Proposed summary

The CLIP loader supports two MLP projector tensor layouts:

- standard LLaVA uses `mm.0.{weight,bias}` and `mm.2.{weight,bias}`;
- Yi-style LLaVA uses `mm.0`, `mm.1`, `mm.3`, and `mm.4` weight/bias pairs.

These tensors are looked up as optional so the loader can distinguish the two
layouts. Validate the selected layout immediately after lookup and before tensor
allocation/read. This prevents an incomplete standard layout from reaching a
later unconditional `mm_2_w` dereference while preserving the complete Yi path.

Any Yi-exclusive tensor selects fail-closed Yi validation. Mixed or partial
layouts are rejected with the first missing tensor named in the error.

## Patch

Apply `targets/clip_mmproj/qualification/patches/validate-mlp-layout.patch` to
`tools/mtmd/clip.cpp`. The patch contains only the proposed loader change; the
metadata and `std::bad_alloc` qualification patches are separate and are not
part of this proposed change.

## Local validation

Validated on 2026-09-09 against llama.cpp
`df750f76bb6126566621803b69ddaeb993be5b08`:

- the standalone proposed patch passed `git apply --check` against the pristine
  index; the compiled qualification build also included the separate metadata
  and `std::bad_alloc` patches described above;
- fresh CPU-only Clang 14 ASan/coverage build: 278/278 steps;
- standard synthetic MLP: 12 descriptors, 12 reads, consumer constructed;
- missing `mm.2.weight`: 11 descriptors, zero reads, explicit rejection;
- complete Yi-style MLP: 16 descriptors, 16 reads, consumer constructed;
- focused qualification suite: 2/2 passed;
- one retained-input replay under CPU 0, 4 GiB, no swap, 5-second input timeout
  and 15-second service deadline: exit 0, no ASan diagnostic.

The synthetic inputs are generated from tracked code and contain no model-derived
data. The retained input and raw private replay details stay local and should not
be included in a public pull request.

## Boundaries

This change validates tensor presence for the two existing MLP layouts. It does
not add tensor shape/dimension validation, numerical inference coverage, or
support for mixed layouts. It makes no security-severity or novelty claim. A
separate non-projector tensor-validation gap is intentionally out of scope.

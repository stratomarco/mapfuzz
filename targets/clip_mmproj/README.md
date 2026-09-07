# CLIP/mmproj target

Status: candidate, incomplete build qualification. The tracked harness calls
`clip_init` with CPU, no warmup and `no_alloc=true`. It reaches metadata handling;
it does not prove real tensor materialization. Its broad exception catches also
limit what a clean run establishes.

`harness/make_clip_seed.py` uses gguf.GGUFWriter to create metadata only, without
tensors. The writer dependency and loader revision must be pinned together before
regenerating a qualification seed. No complete build script or tracked tensor
corpus is available in this checkout.

Next gate: refresh current upstream API and fuzz target list, establish an exact
build environment, generate a valid tensor-carrying seed and demonstrate actual
materialization under caps. Do not assume changing no_alloc alone achieves this.
Historical metadata findings are in docs/FINDINGS.md and evidence/claims.yaml.
Private regression material is not included here.

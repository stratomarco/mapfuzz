# Frontier target map

Forward-looking reconnaissance of emerging ML infrastructure, produced after the
maintained-core result: file loaders and serving runtimes at the center of the
ecosystem (llama.cpp, vLLM, Triton, huggingface_hub, gptqmodel) are hardened at
both the DoS and memory-corruption tiers at their trust boundaries. Novel
findings have therefore moved to newer and more peripheral code. This document
ranks emerging surfaces by where a structure-aware fuzzer with the seam thesis is
most likely to find real, novel defects.

Scoring dimensions (each surface judged against all five):
- young: new enough that a hardening pass has not happened
- trust boundary: loads untrusted artifacts or takes untrusted input
- uncrowded: not already saturated by OSS-Fuzz, pro security teams, or a CVE history
- thesis-fit: a format, loader, or serving path with a producer-consumer seam
- CPU-reachable: exercisable without GPU-only execution

Recon date: 2026-08-28. Re-verify before acting, this space moves monthly.

## Ranked targets

### 1. World-model / VLA / JEPA research runtimes
- young: very. A 2026 explosion (V-JEPA 2, LeWorldModel, VLA-JEPA, WorldVLA, Genie, Alpamayo, stable-worldmodel, a large arXiv volume).
- trust boundary: yes. They load checkpoints and convert datasets (video, action, latent tokens).
- uncrowded: yes. Almost no security attention on this code.
- thesis-fit: yes on the data-conversion and checkpoint-config parsing paths.
- CPU-reachable: much of the conversion and config handling is CPU-side.
- Caveat, and the discipline for this target: the low-hanging fruit is the KNOWN
  pickle / .pt arbitrary-code-execution problem (VLA-JEPA loads a .pt checkpoint,
  configs are YAML pointing at checkpoint paths). That is not a novel finding, it
  is the ecosystem's oldest known issue and the reason safetensors exists. The
  NOVEL surface is their custom data-conversion, tokenization of untrusted video
  or action data, and checkpoint-config handling that is not just pickle. Hunt
  that, not the pickle.
- Candidates: stable-worldmodel (explicitly a platform with data conversion),
  V-JEPA 2 and VLA-JEPA reference runtimes (checkpoint plus config loading).

### 2. MCP-server protocol parsing
- young: yes. MCP scaled to over 97M monthly SDK downloads by April 2026.
- trust boundary: yes. Network JSON-RPC requests and tool responses.
- uncrowded: mixed. The space is heavily researched, but the attention is on
  prompt injection, tool poisoning, and broken authentication (88% of open-source
  MCP servers per one 2026 figure), NOT on the memory-safety and parsing of the
  JSON-RPC and transport layer. The parsing sub-surface may be less examined.
- thesis-fit: yes for the message-parsing and schema-validation layer. The
  prompt-injection and tool-poisoning class is a different, semantic discipline
  and is out of scope for this thesis.
- CPU-reachable: yes.
- Note: keep strictly to the parser / transport / schema layer. The crowded part
  (prompt injection) is not what this fuzzer does.

### 3. New quantization encodings in existing containers
- young: yes for the encodings (NVFP4, MXFP4, MLX 4-bit and 8-bit, new k-quants).
- trust boundary: yes, the dequantization math runs on downloaded weights.
- uncrowded: moderate.
- thesis-fit: yes, the dequant size and block math is exactly the class already
  examined in gguf-py (C-0037) and gptqmodel (C-0046).
- CPU-reachable: the CPU dequant paths are.
- Caveat: the CONTAINER is already hardened (safetensors, GGUF). Only the new
  quant-type dequant math is virgin surface, so this is a narrow target. MLX is
  safetensors-based, so the MLX-specific quant handling, not the container, is the
  surface.

### 4. Niche new formats (CryptoTensors and similar)
- young: yes, but tiny adoption and largely academic so far.
- trust boundary: yes, a new parser over untrusted files.
- uncrowded: yes.
- thesis-fit: yes, new parser.
- CPU-reachable: likely.
- Caveat: low real-world reach today. Worth watching, not worth leading with.

### 5. Edge / on-device runtimes
- Not surveyed in depth this pass. Often C or C++, often newer and less scrutinized
  than server-side. Parked for a later recon.

## Decision

Lead with target 1 (world-model runtimes), the youngest and most uncrowded
surface, and the strongest get-there-early fit. The explicit discipline is to
hunt the novel data-conversion and checkpoint-config parsing surface, not the
already-known pickle / .pt code-execution problem. If a world-model runtime does
novel parsing of untrusted artifact data beyond pickle, that is a genuine frontier
finding. If its only exposure is pickle, that is not novel and is recorded as such.

This map is the reconnaissance output. The M0 that follows selects a concrete
world-model repository and applies the standard method: find the untrusted trust
boundary, check whether the seam is guarded, calibrate severity honestly.

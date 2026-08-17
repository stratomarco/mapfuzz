# ML model supply chain: a trust-boundary threat model

Status: living document. Every stage row cites established evidence (claim IDs,
M0 entries) or is explicitly marked UNVERIFIED (needs an M0 check) or UNPROBED
(no fuzzing attempted). Nothing here asserts a security status we have not
checked.

## Scope

In scope: the path a model artifact travels from author to running inference,
treating each hand-off as a trust boundary and each downloaded artifact as
attacker-controlled input. The animating question is the same as the rest of
mapfuzz: a model file downloaded from a public hub is untrusted input fed into a
parser or loader.

Out of scope (different disciplines, noted so the boundary is clear):
- Training-data poisoning and weight backdoors (a model-behavior problem, not a
  parser/loader problem; covered by separate essays, not this fuzzing work).
- Author-account compromise and hub infrastructure security (an operational /
  identity problem, not an artifact-parsing problem).
- Building code-execution or config-injection vectors. Scope is defect
  demonstration: crash, DoS, divergence, memory-safety violation.

## The pipeline as a trust-boundary graph

Each arrow is a trust boundary: a point where data crosses from a
less-trusted producer to a consumer that parses or acts on it.

    author trains
       | (export / conversion scripts)
       v
    convert / export  ---- HF format -> framework format, GGUF, etc.
       | (quantization tools)
       v
    quantize          ---- GPTQ / AWQ / GGUF-quantize / bitsandbytes
       | (upload)
       v
    hub artifact
       | ===== DOWNLOAD (primary trust boundary) =====
       v
    cache / verify    ---- hash check, snapshot_download, symlink cache
       |
       v
    metadata parse    ---- config.json, tokenizer.json, model card, info.json
       |
       v
    format load       ---- GGUF / safetensors / pickle / flax / npz container
       |
       v
    tensor materialize ---- declared dims -> allocation, tensor validation
       |
       v
    runtime           ---- chat-template engine, multimodal projector, adapters/LoRA

## Per-stage analysis

Legend for OSS-Fuzz: SATURATED (a fuzz target covers it), GAP (project in
OSS-Fuzz but this entry point is not a target), UNFUZZED (not in OSS-Fuzz),
UNVERIFIED (we have not checked).

### Stage: convert / export
- Input: an untrusted HF model directory (config.json, tokenizer files, weight
  shards, custom code refs). Consumed by conversion scripts.
- Attacker-reachable: YES. Downloaded models are routinely re-converted (e.g. HF
  -> GGUF) by end users and pipelines, so conversion runs on untrusted input.
- OSS-Fuzz: CONFIRMED GAP. llama.cpp is the only relevant project in OSS-Fuzz
  (verified against the full 1372-project list, 2026-08-17), and its target list
  does not include convert_hf_to_gguf.py or the gguf-py writer.
- Bug classes possible: unbounded allocation from declared shapes/counts,
  path traversal (weight-file naming), unsafe deserialization if the converter
  imports model-defined code, integer overflow in shape math, resource
  exhaustion.
- mapfuzz status: UNPROBED. No target. HYPOTHESIZED PRIORITY (left-half gap).

### Stage: quantize
- Input: a loaded/converted model plus quantization config. Consumed by GPTQ /
  AWQ / GGUF-quantize / bitsandbytes tooling.
- Attacker-reachable: YES (same re-quantization-of-downloaded-models reasoning).
- OSS-Fuzz: CONFIRMED GAP. auto-gptq, autoawq, bitsandbytes, optimum are none of
  them OSS-Fuzz projects (verified against the full project list, 2026-08-17).
- Bug classes: shape/scale arithmetic overflow, unbounded allocation, div-by-zero
  in scale/zero-point computation, OOB in block/group indexing.
- mapfuzz status: UNPROBED. HYPOTHESIZED PRIORITY.

### Stage: download / cache / verify
- Input: hub responses, file names, symlink targets, hash metadata. Consumed by
  huggingface_hub snapshot_download / caching layer.
- Attacker-reachable: YES for a malicious/compromised repo (file names, sizes,
  symlink layout are repo-controlled).
- OSS-Fuzz: CONFIRMED GAP. huggingface_hub is not an OSS-Fuzz project (verified
  against the full project list, 2026-08-17).
- Bug classes: path traversal / symlink escape in cache layout, zip-slip-style
  extraction issues, resource exhaustion (declared file counts/sizes).
- mapfuzz status: UNPROBED. HYPOTHESIZED PRIORITY (distinct class: filesystem,
  not parsing).

### Stage: metadata parse
- Input: config.json, tokenizer.json, model card, dataset info.json.
- Attacker-reachable: YES (ship inside the repo).
- OSS-Fuzz: mixed. GAP/UNFUZZED for the specific parsers we targeted.
- Bug classes: type confusion, unbounded allocation from declared counts,
  unhandled-exception robustness gaps.
- mapfuzz status: PROBED, well mapped.
  - tokenizers: findings C-0001, C-0002, C-0003 (panic-on-load class; reported).
  - transformers config: negative C-0032 (robust in scope).
  - lerobot info.json: non-findings C-0022, C-0023 (robustness gap; latent
    allocation dead on its caller).

### Stage: format load (container parse)
- Input: the model container file itself (GGUF, safetensors, pickle, flax, npz).
- Attacker-reachable: YES (the primary downloaded artifact).
- OSS-Fuzz: SATURATED for several mainstream formats (numpy, hdf5, onnx,
  sentencepiece; see M0 strategic note). NOTE: safetensors is NOT a dedicated
  OSS-Fuzz project per the 2026-08-17 list; the earlier M0 note should be
  re-checked. GAP/UNFUZZED for newer loaders.
- Bug classes: integer div-by-zero, OOB, type confusion, memory corruption.
- mapfuzz status: PROBED, well mapped.
  - GGUF: negative C-0030-tier (hardened; 0001 was a known duplicate).
  - pytorch weights_only: negative C-0030 (robust).
  - flax checkpoint: non-finding + negative (loosely typed, no crash).

### Stage: tensor materialize
- Input: declared tensor dims/counts from the container, used to allocate and
  validate actual tensors.
- Attacker-reachable: YES.
- OSS-Fuzz: GAP for the loaders we examined (their fuzz targets stop at container
  parse, not multimodal/tensor materialization).
- Bug classes: unbounded allocation from declared dims (confirmed), OOB on
  dim/tensor mismatch, integer overflow in size math, POSSIBLE memory corruption.
- mapfuzz status: PARTIALLY PROBED.
  - clip/mmproj: finding C-0014 (block_count unbounded allocation).
  - clip hparam surface: negative C-0035 (22.8M runs clean).
  - UNPROBED sub-surface: the tensor-loading path reached only with a
    tensor-carrying seed (noted in C-0035 boundary). HYPOTHESIZED depth probe.

### Stage: runtime (template / projector / adapters)
- Input: chat templates, multimodal projector metadata, LoRA/adapter files.
- Attacker-reachable: YES (ship in tokenizer configs / as separate artifacts).
- OSS-Fuzz: GAP (fuzz_apply_template varies context, not template text; mtmd
  loader not in the target list).
- Bug classes: unbounded recursion (stack overflow), div-by-zero, type confusion,
  unbounded allocation.
- mapfuzz status: PROBED, yielded.
  - minja: findings C-0010, C-0011 (recursion DoS, div/mod-by-zero; reported).
  - clip scalar getters: finding C-0013 (type-confusion abort; reported).
  - UNPROBED: LoRA/adapter loading.

## What falls out: prioritized target list (derived, not asserted)

Ranking by: attacker-reachable AND (OSS-Fuzz gap/unfuzzed OR unprobed by us)
AND a plausible non-trivial bug class. Left-half stages dominate because the
whole project so far has been right-half.

1. convert / export tooling (convert_hf_to_gguf.py and peers). Reachable,
   likely unfuzzed, unprobed, rich bug surface (shape math, unsafe imports,
   path handling). NEEDS M0 to confirm OSS-Fuzz status. Highest expected value.
2. download / cache / verify layer (huggingface_hub). Distinct filesystem class
   (path traversal / symlink), not parsing; a genuinely different oracle.
   NEEDS M0.
3. quantization tooling. Reachable, arithmetic-heavy, likely unfuzzed. NEEDS M0.
4. tensor-materialize depth probe (clip tensor-loading path). Known-reachable,
   harness 90 percent built; the cheapest test of the "can we reach a
   memory-corruption class, not just DoS" question. A single time-boxed
   experiment, a data point in this taxonomy either way.
5. LoRA / adapter loading. Reachable runtime artifact, unprobed.

## How this maps the project's contribution

The right half of the chain (metadata parse, format load, tensor materialize,
runtime) is now well mapped: findings where loaders are newer/less-hardened,
rigorous negatives where they are mature. The left half (convert, quantize,
download/cache) is entirely unprobed and is where an attacker-reachable,
likely-unfuzzed surface remains. That asymmetry is the next research direction
and the spine of a systematization: the ML supply chain has been fuzzed at the
point of loading but not at the points of conversion and distribution, even
though both run on downloaded, untrusted artifacts.

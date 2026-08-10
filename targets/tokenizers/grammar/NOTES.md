# tokenizer.json structure-aware mutation notes

`tokenizer.json` is a JSON document, so byte-level mutation quickly produces invalid JSON that fails at the serde boundary and never reaches the interesting construction logic. A structure-aware approach keeps the JSON valid while mutating the fields that drive the dangerous paths. This file records the structure and the high-value targets; a mutator (a custom `arbitrary`-based generator, or a JSON-aware mutator) is the next step.

## Top-level structure

A tokenizer.json has these top-level keys, most nullable:

- `version`: string.
- `truncation`, `padding`: nullable config objects.
- `added_tokens`: array of token objects (id, content, flags).
- `normalizer`: nullable, tagged by `type` (e.g. NFC, NFD, Sequence, Replace, ...).
- `pre_tokenizer`: nullable, tagged by `type` (Whitespace, ByteLevel, Split, Sequence, ...).
- `post_processor`: nullable, tagged by `type` (TemplateProcessing, BertProcessing, ...).
- `decoder`: nullable, tagged by `type`.
- `model`: the core, tagged by `type` (WordLevel, BPE, WordPiece, Unigram), carrying `vocab` and possibly `merges`.

Most components are internally tagged enums (`{"type": "...", ...}`), so the `type` string selects a deserialization path. Invalid or unexpected `type` values, and valid types with malformed payloads, are both worth reaching.

## High-value mutation targets

- `model.type` and each component `type`: valid tags with missing or malformed required fields exercise each variant's deserializer and constructor.
- `model.vocab`: very large vocabs, duplicate ids, non-contiguous or negative-looking ids, huge token strings.
- `model.merges` (BPE): malformed merge entries, merges referencing tokens absent from the vocab, enormous merge tables.
- `added_tokens`: ids that collide with or exceed the vocab, huge `content`, contradictory flags.
- `post_processor` TemplateProcessing: templates referencing sequences or special tokens that do not exist, which is a construction-time consistency surface.
- `normalizer` / `pre_tokenizer` Sequence: deep nesting to probe stack usage.
- numeric fields (ids, ranks, sizes, unk_id, dropout): boundary and out-of-range values.

## Approach

1. Custom generator with the `arbitrary` crate: derive or hand-write an `Arbitrary` impl that emits structurally valid tokenizer.json variants, mutating one field class per input while keeping the document parseable. Fast, self-contained, and integrates directly with cargo-fuzz via `fuzz_target!(|t: TokenizerConfig| ...)`.
2. JSON-aware byte mutator: mutate the seed as a JSON tree, preserving syntactic validity. Reuses seeds directly but is less targeted than a typed generator.

Start with option 1 focused on the `model` variants (WordLevel, BPE, WordPiece, Unigram), since the model constructor is where vocab and merge consistency is enforced and where the richest logic lives.

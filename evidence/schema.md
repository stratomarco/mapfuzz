# Claim schema

Each claim in `claims.yaml` is a record with these fields. Required fields are
marked (req).

## Fields

- `id` (req): stable identifier, `C-NNNN`. Never reused, never renumbered.
- `date` (req): ISO date the claim was established (YYYY-MM-DD).
- `target` (req): what was examined (e.g. `tokenizers`, `minja`, `pytorch`,
  `flax_checkpoint`, `chassis`, `project`).
- `entry_point`: the specific function/surface (e.g. `Parser::parse`,
  `msgpack_restore`), when applicable.
- `statement` (req): the claim itself, one sentence, precise.
- `kind` (req): one of
  - `finding`      a real defect (crash/DoS/vuln) that reproduces
  - `negative`     a robust-surface result (no defect found under stated effort)
  - `non-finding`  a defect-shaped observation deliberately NOT counted (with why)
  - `method`       a reusable technique or lesson
  - `audit`        an M0 / prior-art / scope determination
  - `correction`   a revision of an earlier claim
- `confidence` (req): one of
  - `verified`     reproduced, or cross-checked against a second source/version
  - `observed`     a single data point, not yet reproduced
  - `inferred`     reasoned from other claims/source, not directly observed
- `provenance` (req): list of how it is known, each tagged:
  - `source-read:<path/detail>`   read from primary source
  - `sandbox-run:<detail>`        executed in Claude's sandbox
  - `machine-run:<detail>`        executed on the researcher's machine
  - `claim:<id>`                  derived from another claim
- `observation` (req): the raw result, verbatim where load-bearing (run counts,
  exit codes, coverage, trace lines, source quotes).
- `boundary` (req): what this claim does NOT establish. The honesty field.
- `severity`: for findings/non-findings, calibrated (see glossary). Omit otherwise.
- `status`: `active` (default) | `superseded:<id>` | `embargoed` | `reported`.
- `refs`: pointers to files (finding docs, disclosure reports, harness paths).

## Rules

- One claim, one statement. If you want to assert two things, write two claims.
- `boundary` is never empty. Every result has a limit; state it.
- A `negative` must state the effort (runs, environment) that bounds it. "Robust"
  with no effort figure is not a claim.
- A `finding` must cite a reproduction (`verified`) or be marked `observed` until
  reproduced.
- `non-finding` must say in `boundary` why it is not counted (e.g. "UBSan-only,
  no crash in release").
- Provenance tags distinguish sandbox from on-machine runs, because they have
  different weight (sandbox cannot install torch; on-machine ran 23M+ campaigns).

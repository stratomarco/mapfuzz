# Methods (referenced by claims)

Reusable techniques and disciplines. Each is also a claim (C-0050..C-0054) with
provenance; this file is the readable index.

- M0 audit before building: check OSS-Fuzz membership and in-repo fuzzers, verify
  the entry point from source, probe that an input LOADS before campaigning.
  (Ruled out numpy, HDF5/Keras; selected GGUF, tokenizers, flax, minja.)
- Structure-stable encoding: fixed-layout byte decode so one flipped byte changes
  one field. Pays off only on rich/branchy surfaces. (C-0050)
- Dedup by fault LOCATION, not artifact count. (C-0051)
- Non-sanitized confirmation: a UBSan flag is not a finding until it crashes a
  release -O2 build. (C-0052)
- Corpus hygiene: a stored crasher re-crashes on startup replay; minimize
  (-merge=1) or restart from seeds. (C-0053)
- Embargoed fuzz-blockers: to fuzz past a known unreported finding, patch the
  recommended fix into the vendored dependency and embargo it; confirm reports
  against pristine upstream only. (C-0054)
- Severity calibration is a value: do not inflate robustness nits or UBSan-only
  UB into findings alongside real crashes.
- Coordinated disclosure: reproducers are unpublished exploits; keep embargoed
  until fixed; report privately with a fix and a crediting request.

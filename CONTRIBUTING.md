# Contributing

## Adding a format target

1. Run the M0 audit for the format (see `docs/M0-baseline-audit.md`): check upstream and OSS-Fuzz for existing harnesses and record unreached load paths.
2. Create `targets/<format>/` with the standard layout: `harness/`, `build.sh`, `corpus/`, `grammar/`, `README.md`.
3. Verify the loader entry point against the upstream source at a pinned commit. Record the commit in `build.sh` and the target README. Do not assume signatures from memory.
4. Gate every harness accessor on the type the loader reports, so the harness never causes a false positive.
5. Seed corpus must be synthetic. No proprietary weights.
6. Instrument with coverage plus AddressSanitizer at minimum; add UndefinedBehaviorSanitizer for the integer and type-confusion classes.

## Standards

- Findings follow `SECURITY.md`. Reproducers stay in gitignored `PRIVATE_findings/` until disclosed.
- Pin upstream commits for reproducibility. A finding must reproduce from its minimized input on the pinned toolchain and commit.
- Output artifacts carry no tool-authorship metadata.

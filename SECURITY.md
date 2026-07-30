# Security policy

## Findings this project produces

This tooling finds vulnerabilities in third-party software (the model-artifact loaders under test). Those findings are handled under coordinated disclosure:

1. Report privately to the upstream maintainer of the affected loader first.
2. Give a reasonable embargo for a fix to ship.
3. Withhold public reproducers until a fix is released or the embargo lapses.

Live crash reproducers and unpublished finding writeups live in a gitignored `PRIVATE_findings/` directory. They must never be committed to a public remote before disclosure. Treat a reproducer as an unpublished exploit.

## Reporting a vulnerability in this project

If you find a defect in the harnesses, build scripts, or CI configuration of this project itself, open a private report to the maintainer rather than a public issue.

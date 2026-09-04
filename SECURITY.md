# Security policy

## Findings this project produces

This tooling finds vulnerabilities in third-party software (the model-artifact loaders under test). Those findings are handled under coordinated disclosure:

1. Report privately to the upstream maintainer of the affected loader first.
2. Give a reasonable embargo for a fix to ship.
3. Withhold public reproducers until a fix is released or the embargo lapses.

Live crash reproducers and unpublished finding writeups live in a gitignored `PRIVATE_findings/` directory. They must never be committed to a public remote before disclosure. Treat a reproducer as an unpublished exploit.

## Reporting a vulnerability in this project

If you find a defect in the harnesses, build scripts, or CI configuration of this project itself, report it privately rather than opening a public issue.

Preferred route: use GitHub Private Vulnerability Reporting. Go to the repository Security tab and choose "Report a vulnerability", which opens a private advisory visible only to the maintainer.

Fallback: email maconstantino@gmail.com.

Please include what to reproduce, the affected revision, and the expected versus observed behavior. This project follows coordinated disclosure: reproducers are treated as unpublished exploits and are withheld publicly until a fix ships or an embargo lapses.

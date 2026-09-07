# Chassis

Run capped libFuzzer/Atheris campaigns with `python3 -m chassis.campaign`.
See [TARGETS.md](../docs/TARGETS.md#local-execution) for the command and contract.
The runner saves logs and exit status locally. Every artifact (including unknown
prefixes), nonzero exit, timeout or recognized diagnostic fails the run.

`python3 -m chassis.triage reports/` deduplicates by fault class and source
location. This can merge distinct root causes at one location, so investigate
buckets manually. `real` means worth investigating, not a verified vulnerability.
`review` includes assertions, enum errors, arithmetic faults and exceptions.
Every bucket and unparsed report fails the gate; missing/empty report input also
fails. There are no allowlisted blockers. Normal campaign success is established
by the runner, not by an empty triage directory.

The resource oracle uses a separate process with an address-space limit and
wall-clock deadline. MemoryError is `exhausted`; timeout is independent; death
without a message is `child-error`, not presumed OOM. A hostile input must raise
within caps by default. `allow_bomb_ok=True` is an explicit policy for loaders
that safely ignore a declaration. Any exception is a resource rejection, not
proof of semantic correctness. Cap/startup failures cannot pass.

CI tests malformed evidence, execution failures, artifact classes, unknown reports,
resource outcomes and synthetic probes through the real stdlib JSON parser.
No model-loader protection is established by the oracle self-test.

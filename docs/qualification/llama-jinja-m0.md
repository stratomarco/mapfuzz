# llama.cpp Jinja M0 review packet

## Identity and scope

- Package ID and objective: R6-LLAMA-JINJA-M0-2026-09-10; determine whether a
  bounded target around current llama.cpp `common/jinja` parsing, rendering and
  resource behavior has a defensible uncovered consumer boundary.
- Author/model and independent reviewer: Codex performed the source and public
  coverage review. Independent review was not run. The author checked the
  decision twice against pinned source and separately retrieved official
  llama.cpp and OSS-Fuzz records; that is corroboration, not independent replay.
- Date, base SHA, implementation SHA or working-diff identity: 2026-09-10;
  `dda7ce84382f91ad5c992974a29bf8d99e45cea1`; this report, roadmap, target
  inventory and qualification-manifest working diff.
- Worktree/branch and exact-head CI link/status:
  `/mnt/f/mapfuzz/audit-hardening-dev`, `daybreak-llama-jinja-m0`; hosted CI is
  unavailable because the local branch was not pushed. Local repository checks
  are recorded below.
- Disposition: **M0-STOP**
- What this disposition establishes and does not establish: current official
  source confirms a distinct `common/jinja` lexer, parser and runtime on the
  server chat-template route. The pinned OSS-Fuzz chat-template harness calls a
  documented legacy API that does not use Jinja, so that public harness does not
  cover the current engine. The same current engine already has substantial
  public fuzz-style testing and same-boundary crash/resource prior art, including
  open or closed-unmerged guards. Without a comparable maintained harness,
  corpus and coverage map, a generic replacement campaign cannot establish
  complementary novelty. This is not a new finding, proof of complete coverage,
  or authorization to build or fuzz.

## M0 and novelty boundary

| Source | Immutable revision and link | Retrieved date | Relevant path/entry point | Observation |
|---|---|---|---|---|
| Current loader/parser | llama.cpp [`72797e89198ab564fd0e6baa54ab196e8dd1d884`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/common/chat.h#L51-L68) | 2026-09-10 | `common_chat_template`; `jinja::lexer::tokenize`; `jinja::parse_from_tokens` | A model-supplied or overridden template is tokenized and parsed into a `jinja::program` during chat-template initialization. This is separate from the legacy public C API. |
| Current runtime/consumer | same revision | 2026-09-10 | [`common_chat_template_direct_apply_impl`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/common/chat.cpp#L895-L955); [`server-common.cpp`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/tools/server/server-common.cpp#L1335-L1344) | Messages, tools and extra context become Jinja globals; the runtime executes the parsed program and gathers rendered parts. The server consumes the resulting prompt, grammar and parser state. |
| Public fuzz build and harness | OSS-Fuzz [`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`](https://github.com/google/oss-fuzz/blob/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects/llamacpp/build.sh#L51-L69) | 2026-09-10 | [`fuzz_apply_template.cpp`](https://github.com/google/oss-fuzz/blob/3209d05c48ad1232ab0c5797f6ed31a1486c2a80/projects/llamacpp/fuzzers/fuzz_apply_template.cpp#L18-L38) | OSS-Fuzz compiles eight fuzzer source files and enables six here. The chat-template fuzzer mutates one template and six messages, then calls `llama_chat_apply_template`. |
| Public API distinction | llama.cpp `72797e8` | 2026-09-10 | [`include/llama.h`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/include/llama.h#L1213-L1229); [`src/llama.cpp`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/src/llama.cpp#L509-L537) | The API explicitly says it does not use a Jinja parser and only supports predefined templates. Unknown templates return `-1`; recognized templates use the legacy renderer. The OSS-Fuzz harness therefore does not reach `common/jinja`. |
| In-tree fuzz-style coverage | llama.cpp `72797e8` | 2026-09-10 | [`tests/test-jinja.cpp`](https://github.com/ggml-org/llama.cpp/blob/72797e89198ab564fd0e6baa54ab196e8dd1d884/tests/test-jinja.cpp#L2296-L2357) | The current tree directly exercises lexer, parser and runtime with a fixed seed, 100 iterations and malformed, arithmetic, recursive-macro and built-in cases. This is deterministic crash regression coverage, not a maintained coverage-guided campaign or proof of completeness. |
| Parser/runtime resource prior art | open [PR 19085](https://github.com/ggml-org/llama.cpp/pull/19085), closed-unmerged [PR 26387](https://github.com/ggml-org/llama.cpp/pull/26387), closed-unmerged [PR 24140](https://github.com/ggml-org/llama.cpp/pull/24140) | 2026-09-10 | parser and macro recursion; `range()` materialization | Public records already propose recursion guards and a `range()` cap. Pinned source still constructs the full range without a cap and recursively executes macro bodies without a call-depth counter. Reproducing these conditions would be rediscovery, not a mapfuzz finding. |
| Crash/arithmetic prior art | completed [issue 20911](https://github.com/ggml-org/llama.cpp/issues/20911), merged [PR 20552](https://github.com/ggml-org/llama.cpp/pull/20552), not-planned [issue 25282](https://github.com/ggml-org/llama.cpp/issues/25282), closed-unmerged [PR 26386](https://github.com/ggml-org/llama.cpp/pull/26386) | 2026-09-10 | malformed parser states; null dereference; filter assertion; `divisibleby` | The same parser/runtime boundary has public null-binding/null-dereference, reachable abort and integer-remainder reports. Pinned `test_is_divisibleby` still performs `%` without a zero or `INT64_MIN % -1` guard. These are public prior art, not new observations. |
| String/output resource prior art | completed [issue 24555](https://github.com/ggml-org/llama.cpp/issues/24555), merged [PR 27034](https://github.com/ggml-org/llama.cpp/pull/27034) | 2026-09-10 | empty-delimiter string methods; `gather_string_parts` | Public reports cover hang/OOM behavior and quadratic output gathering in the current engine. The latter fix is present at the pinned head. These records further overlap the proposed parser/runtime/resource scope. |

The deployment-dependent trust boundary is a model-provided or operator-selected
chat-template string plus request messages, tool schemas and extra context. The
supported current consumer sequence is template selection, lexing, parsing,
capability analysis, request normalization, runtime execution, rendered-output
gathering and server prompt/grammar/parser use. A parser-only target would not
establish end-to-end server behavior, while a full target would need to state
which message, tool, autoparser and output milestones it observes.

There is a concrete public OSS-Fuzz gap: `fuzz_apply_template` reaches only the
legacy predefined-template implementation. That observation is narrower than a
claim that current Jinja is unfuzzed. Current upstream source itself includes a
deterministic fuzz-style suite that directly runs the lexer, parser and runtime,
and official project records document multiple failures or proposed guards in
the same parser/runtime/resource boundary. GitHub issue searches are incomplete;
the report does not infer absence of additional private, ad hoc or differently
named work.

The intended new target cannot presently be separated from that prior art. Its
most obvious high-value resource dimensions—recursive parsing/macro calls,
`range()` materialization, arithmetic exceptional cases, string-loop behavior
and output aggregation—already have public reports or patches. The exact prior
coverage-guided harness, corpus and coverage map are unavailable. Starting a
generic campaign would therefore risk immediate rediscovery and would not meet
the roadmap requirement to demonstrate complementary coverage before compute.

## Reproduction environment

Source-only reconnaissance ran on Ubuntu 22.04.5 WSL2 x86_64, Linux
6.6.87.2, with Git 2.34.1, Python 3.10.12 and curl 7.81.0. Official heads were
resolved with `git ls-remote`; an exact source archive, pinned source/API files
and OSS-Fuzz contents responses were retained under ignored
`.runs/llama-jinja-m0-2026-09-10/` and hashed with SHA-256.

The exact llama.cpp head was
`72797e89198ab564fd0e6baa54ab196e8dd1d884`, committed 2026-09-10 07:06:07Z.
The source tree response named tree
`4fe7b3d13209c8d5801994ea6b2ed733b861a793`, contained 3,943 entries and was
not truncated. The exact OSS-Fuzz head was
`3209d05c48ad1232ab0c5797f6ed31a1486c2a80`. No dependency, compiler,
submodule, package, container or binary was installed or built. No upstream
patch exists. Fresh-build reproduction, sanitizer selection, binary hashes,
seed hashes and dependency locks are **not run** because M0 stopped first.

## Semantic controls

| Benign/control input and hash | Expected milestone | Observed milestone/count | Source probe location | Exit/result | Local evidence |
|---|---|---|---|---|---|
| Valid model chat template plus messages/tools | lex, parse, runtime execute, gather output, server consume prompt/grammar/parser | not run | not implemented | not run | M0 stopped before build/seed |
| Malformed template | distinct lexer/parser rejection before runtime | not run | not implemented | not run | Pinned source/tests inspected only |
| Valid template with missing/invalid context value | parse succeeds; runtime failure or defined undefined-value behavior remains distinct | not run | not implemented | not run | M0 stopped before build/seed |

No harness, probe, seed or new target directory was created. Source inspection
does not claim that tokenization, AST construction, a successful render, or a
server response alone proves every later autoparser or generation consumer.

## Bounded runs and resource behavior

Qualification and mutation batches are **not run**. The shared one-worker,
4 GiB/no-swap, 5-second input, 60-second campaign and 90-second outer caps were
therefore not exercised. Attempts, accepted inputs, rendered inputs, new
states/functions, elapsed time and peak resident memory are all **unavailable**,
not zero.

| Batch | Duration/limits | Attempts | Accepted | Materialized | New states/functions | Result/log hash |
|---|---|---|---|---|---|---|
| 1 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 2 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |
| 3 | not run; M0 stop | unavailable | unavailable | unavailable | unavailable | unavailable |

## Independent review

- Exact commands replayed by reviewer and environment differences: independent
  review was not run. The author repeated official head resolution, immutable
  source/API checks, direct source-to-harness comparison and separate official
  contents inventories for the OSS-Fuzz project and its `fuzzers/` directory.
- Benign/control outcomes compared with the author's report: not applicable; no
  build, harness, seed or control ran because M0 stopped.
- Core tests, workflow results and changed-code tests: two complete Python 3.10
  passes each reported evidence 5/5, chassis 16/16 and triage 3/3; both resource
  oracle self-tests, evidence schema/render checks, repository/manifest checks
  and `git diff --check` passed. Python 3.12 resource tests passed 5/5 twice.
  Hosted CI is unavailable for this unpushed branch.
- Exception handling, resource cleanup and instrumentation diff checked: no
  target, build, patch, instrumentation or runtime resource exists; only this
  report and portfolio status documentation changed.
- Private artifacts and accidental disclosures excluded from review diff: all
  source/API snapshots are public and ignored under `.runs/`. No reproducer,
  private artifact or credential was created or added.
- Claims/render synchronization and scope wording checked: public OSS-Fuzz
  absence is limited to the inspected harness inventory; prior art is explicitly
  separated from mapfuzz observations; no evidence-ledger claim is proposed.
- Unresolved contradictions or limitations: current public Jinja is not reached
  by the pinned OSS-Fuzz chat-template harness, but upstream has in-tree
  fuzz-style tests and public same-boundary reports. Their exact continuous fuzz
  coverage, corpus and current operation remain unavailable. Search results are
  not exhaustive, and public conditions were not reproduced locally.

## Decision

**M0-STOP.** The current llama.cpp Jinja engine is a real, supported server
consumer and the pinned OSS-Fuzz chat-template harness demonstrably misses it.
That gap alone is insufficient to qualify a new target. Current upstream source
directly exercises lexer/parser/runtime with deterministic malformed-input tests,
and public project records already cover the obvious parser, recursion,
materialization, arithmetic, string-loop and output-growth failure classes. A
generic target cannot presently demonstrate complementary coverage or avoid
known rediscovery.

Allocate **no build or fuzz compute**. The bounded next action is maintainer
review of this stop followed by explicit selection of the LeRobot-composition
M0, which must independently establish its own current consumer boundary. Do not
create a current-Jinja target directory, reproduce public reports, contact
maintainers or silently switch targets in this package.

## Local evidence inventory

All paths are ignored and contain only public source or API responses:

- llama.cpp commit and complete tree responses: `commit.json`, SHA-256
  `a0359b5243a529a4f7e9e7a7f0e559f2adabdbe0c3e3b307a3e907f40d6891ec`;
  `tree.json`, SHA-256
  `5cdec4a04fcec20da9a2095e31355bbec94846a3f8020d9bea379c71bc5cc6a2`.
- Exact source archive: `llama.cpp-72797e8.tar.gz`, SHA-256
  `327013461b49f9f24f51132c396addc9bea79069641f209a12f91a52599dae1c`.
- OSS-Fuzz build and harness: `oss-fuzz-build.sh`, SHA-256
  `b5b385618b756a4b7ec9578dfef5ff81f63d31e3e3e2e341d08d1ecd23213ba2`;
  `oss-fuzz-apply-template.cpp`, SHA-256
  `10d1de6fa8b259d407bab5fe01d10fb9e0eefca7a09dbf5f544e634695af2410`.
- Official OSS-Fuzz contents responses: `oss-fuzz-project-contents.json`,
  SHA-256 `8d21d40d4ed2b820dc30733b622b647ce01825a7d05d9a369d232a805ac8ad45`;
  `oss-fuzz-fuzzers-contents.json`, SHA-256
  `4ae9fb2f1401c0a2f880f9040028165d3c95b92451d4e3b40638e0518f1ad249`.
- Selected official project records are `pr-{19085,20552,24140,26386,26387,27034}.json`
  and `issue-{20911,24555,25282,28249}.json`; their hashes are retained locally.
  Search snapshots are not treated as exhaustive.

No external action was taken: no push, merge, publication, pull request, issue,
message or upstream contact.

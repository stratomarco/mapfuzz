# Target: minja chat-template parser (llama.cpp's C++ Jinja engine)

## Trust boundary

A chat template ships INSIDE a model's tokenizer config and is parsed and
executed at inference time. llama.cpp reimplements Jinja from scratch as minja, a
header-only C++ interpreter. Parsing an untrusted template is a
download-to-load-to-execute boundary. This target fuzzes the memory-safety
surface (crashes / OOB / UB under ASan+UBSan), the same shape as GGUF, not a
sandbox-escape/RCE hunt.

## Loader under test

- Entry point: minja::Parser::parse(const std::string&, const Options&) (verified,
  minja.hpp). Fuzzes parse (bytes -> template AST). A deeper harness can
  parse+render against a context to exercise the interpreter.

## M0

jinja2 (the Python engine) is in OSS-Fuzz, but minja (the C++ reimplementation)
is NOT, nor are the consumers (llama-cpp-python, ollama, vllm, transformers all
404). No fuzzer in the minja repo. Open ground.

## Findings

- LOW-SEVERITY UB (real): minja::Options declares `bool trim_blocks`,
  `lstrip_blocks`, `keep_trailing_newline` with NO default initializers. The
  natural usage `minja::Options opts;` leaves them uninitialized; parse then reads
  them (UBSan: "load of value 127, which is not a valid value for type 'bool'" at
  minja.hpp:2604). Real UB in the library's API surface; fix is one line
  (`= false` defaults). Severity is low and caller-dependent: whether it is
  attacker-reachable depends on how llama.cpp constructs Options (a careful caller
  sets all three). Reportable as a minor upstream correctness bug, not a vuln in
  the class of a memory-corruption or attacker-controlled crash. The harness
  initializes Options explicitly so it can test PARSING rather than re-tripping
  this on every input.

## Status

Built and validated in-sandbox (clang 18, libFuzzer+ASan+UBSan). With Options
initialized, a 90s campaign ran clean over 93k runs BUT with rich, growing
coverage (cov 2709, ft 8158, 645-entry corpus), unlike the shallow corridors of
other targets. This is a genuinely deep, branchy C++ parser with room to search:
a long campaign with the persistent corpus is warranted and is the most promising
open surface in the project. Next: a parse+render harness (executes the template,
deeper interpreter surface).

## Build and run

```
./build.sh
./fuzz_minja -max_total_time=600 -rss_limit_mb=4096 corpus/
```

## Second harness: fuzz_render.cc (interpreter surface)

fuzz_parse covers parsing (bytes -> AST). fuzz_render goes deeper: it parses the
input and RENDERS it against a realistic chat context (messages, tools, common
template variables), exercising the interpreter, expression evaluation, filters,
loops, the Value type system. Rendering reaches ~50% more code than parsing
(cov ~4272 vs ~2835 in a 2-minute in-sandbox run) and is the deepest, most
fertile surface in the project. Warrants a long campaign.

Both harnesses bound input nesting depth (skip very deep bracket/brace nesting)
so the campaign explores the broad surface. Built and validated in-sandbox
(clang 18); both clean over ~95k-98k runs each in short runs, with rich growing
coverage. A long campaign on the render surface is the recommended next step.

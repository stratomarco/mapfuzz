// libFuzzer harness for minja (llama.cpp's C++ Jinja chat-template engine).
//
// Trust boundary: a chat template ships INSIDE a model's tokenizer config and is
// parsed + executed at inference time. llama.cpp reimplements Jinja as minja (a
// header-only C++ interpreter). Parsing an untrusted template is a download-to-
// load-to-execute boundary, and minja is a young from-scratch C++ parser not in
// OSS-Fuzz. This is the memory-safety surface (crashes / OOB / OOM under ASan),
// the same shape as the GGUF target, not a sandbox-escape/RCE hunt.
//
// Entry point verified: minja::Parser::parse(const std::string&, const Options&)
// (minja.hpp). We fuzz parse (bytes -> template AST). A separate deeper harness
// can parse+render against a context to exercise the interpreter.
//
// Scope: defect demonstration (memory-safety / DoS). minja throws
// std::runtime_error for malformed templates; those are clean rejections. A
// finding is an ASan report, an unhandled non-std crash, or a hang.

#include <string>
#include <cstdint>
#include <cstddef>

#include "minja/minja.hpp"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  // Bound input size so pathological but legitimate large templates do not
  // dominate the corpus; parser bugs surface at small sizes.
  if (size > 64 * 1024) return 0;

  std::string tmpl(reinterpret_cast<const char *>(data), size);

  try {
    // NOTE: minja::Options declares its bool members with no default
    // initializers, so `Options opts;` reads uninitialized bools during parse
    // (UBSan: load of non-0/1 into bool at minja.hpp:2604). That is a real
    // low-severity UB bug in minja's API (recorded in README), but it is a
    // per-call constant, not the parser surface. Initialize explicitly so the
    // fuzzer exercises PARSING of untrusted templates rather than tripping the
    // same uninitialized read on every input.
    minja::Options opts;
    opts.trim_blocks = false;
    opts.lstrip_blocks = false;
    opts.keep_trailing_newline = false;
    auto node = minja::Parser::parse(tmpl, opts);
    // Parsing succeeded. We do NOT render here (render needs a context and
    // executes the template); a separate harness covers render. Touch the
    // result so the parse is not optimized away.
    if (node) {
      (void)node.get();
    }
  } catch (const std::runtime_error &) {
    // Expected: minja signals malformed templates via runtime_error.
  } catch (const std::exception &) {
    // Other std exceptions from parsing are also treated as clean rejections.
  }
  // Any non-std crash, ASan violation, or hang is caught by the fuzzer.
  return 0;
}

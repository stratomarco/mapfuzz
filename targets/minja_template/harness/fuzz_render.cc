// libFuzzer harness for minja parse + RENDER (the interpreter surface).
//
// fuzz_parse.cc covers parsing (bytes -> AST). This harness goes deeper: it
// parses the fuzzer input as a template and RENDERS it against a realistic chat
// context, exercising the interpreter (expression evaluation, filters, loops,
// the Value type system, string ops). Rendering does real work with parsed
// structures, so a memory-safety bug is more likely to surface here than in
// parsing alone.
//
// Trust boundary: a chat template ships inside a model config and llama.cpp
// parses AND renders it at inference. Both stages take untrusted template input.
//
// Scope: defect demonstration (memory-safety / DoS under ASan+UBSan). minja
// throws std::runtime_error for malformed templates and bad operations; those
// are clean rejections. A finding is an ASan/UBSan report or a non-std crash.

#include <string>
#include <cstdint>
#include <cstddef>

#include "minja/minja.hpp"

using json = nlohmann::ordered_json;

// Note on the known integer div/mod-by-zero: build.sh compiles this harness with
// -fsanitize-recover=integer-divide-by-zero,float-divide-by-zero, so UBSan logs
// that one check and continues rather than aborting, letting the campaign explore
// past it. No signal handler is used (it conflicted with libFuzzer's own signal
// setup); the recover flag alone is sufficient under the UBSan build we fuzz with.

// Build a realistic chat context once (messages, tools, common variables that
// real chat templates reference), so rendering reaches template logic instead of
// dying immediately on undefined variables.
static minja::Value make_chat_context() {
  json j = {
    {"messages", json::array({
      {{"role", "system"}, {"content", "You are helpful."}},
      {{"role", "user"}, {"content", "Hello"}},
      {{"role", "assistant"}, {"content", "Hi there"}},
      {{"role", "tool"}, {"content", "result"}, {"name", "search"}},
    })},
    {"add_generation_prompt", true},
    {"bos_token", "<s>"},
    {"eos_token", "</s>"},
    {"tools", json::array({
      {{"type", "function"},
       {"function", {{"name", "search"}, {"description", "search the web"}}}},
    })},
    {"tool_calls", json::array()},
    {"loop_messages", json::array()},
  };
  return minja::Value(j);
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
  if (size > 64 * 1024) return 0;

  // Skip inputs past a safe nesting depth so this harness exercises the RENDER
  // surface broadly instead of spending the budget on a single deep parse path.
  {
    int depth = 0, maxd = 0;
    for (size_t i = 0; i < size; ++i) {
      char c = static_cast<char>(data[i]);
      if (c == '(' || c == '[' || c == '{') { if (++depth > maxd) maxd = depth; }
      else if (c == ')' || c == ']' || c == '}') { if (depth > 0) --depth; }
    }
    if (maxd > 200) return 0;
  }

  std::string tmpl(reinterpret_cast<const char *>(data), size);

  try {
    minja::Options opts;
    opts.trim_blocks = false;
    opts.lstrip_blocks = false;
    opts.keep_trailing_newline = false;

    auto node = minja::Parser::parse(tmpl, opts);
    if (!node) return 0;

    auto ctx = minja::Context::make(make_chat_context());
    std::string out = node->render(ctx);   // the interpreter surface
    (void)out.size();
  } catch (const std::runtime_error &) {
    // Expected: malformed template / bad operation.
  } catch (const std::exception &) {
    // Other std exceptions are clean rejections for this harness.
  }
  return 0;
}

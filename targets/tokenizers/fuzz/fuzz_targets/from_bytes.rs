// tokenizers from_bytes fuzz harness.
//
// Target: huggingface/tokenizers, entry point Tokenizer::from_bytes.
// API verified against tokenizer/mod.rs:473 at the pinned crate version:
//   pub fn from_bytes<P: AsRef<[u8]>>(bytes: P) -> Result<Self>
//
// from_bytes runs the full serde deserialization of a tokenizer.json-equivalent
// buffer plus tokenizer construction, with no filesystem access. This is the
// download-to-load trust boundary: a tokenizer file ships with every model and
// is parsed on load.
//
// This is safe Rust, so the target classes are logic faults, not memory
// corruption: panics (unwrap/expect/index-out-of-bounds), unbounded allocation
// from declared sizes, and integer overflow in offset or vocab math. A panic
// reached from untrusted input is a denial-of-service finding.

#![no_main]
use libfuzzer_sys::fuzz_target;
use tokenizers::tokenizer::Tokenizer;

fuzz_target!(|data: &[u8]| {
    let _ = Tokenizer::from_bytes(data);
});

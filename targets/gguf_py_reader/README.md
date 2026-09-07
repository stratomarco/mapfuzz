# gguf-py reader target

Status: archived as mapped; reopen only after meaningful upstream reader changes.

Tracked source: `harness/fuzz_gguf_reader.py` and `harness/make_seed.py`.
The generator creates `corpus/seed.gguf` when run from this directory. It requires
a pinned llama.cpp gguf-py checkout and Python dependency environment, neither of
which is fully locked here. No tracked seed corpus or complete build script is
claimed. The self-test checks trivial rejection only, not valid-seed reachability.

Historical campaigns and source conclusions remain in evidence/claims.yaml.
A fresh campaign needs exact upstream/dependency pins, seed acceptance and
consumer reachability, followed by the capped campaign runner. A reader's clean
exception is not a guarantee that it correctly handles all malformed files.

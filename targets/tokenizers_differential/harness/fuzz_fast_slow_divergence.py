"""Cross-implementation differential oracle for tokenizer behavior.

A new KIND of oracle: not "does it crash" but "do two implementations that should
agree, disagree." The fast (Rust-backed) and slow (pure-Python) tokenizers in
transformers are built from the SAME vocab and are contractually supposed to
produce identical token ids for any input. A divergence means the same text
becomes different tokens depending on which stack loads the model. That is a
security-relevant supply-chain bug: a guardrail, filter, or safety classifier
tuned on one tokenization can be silently bypassed under the other.

Oracle: build a matched fast/slow pair from one vocab (done once). For each fuzzed
input string, encode with both; if the token ids differ, that is a finding. No
crash required. Both implementations rejecting the input the same way, or both
producing the same ids, is agreement (not a finding).

Scope: correctness/divergence demonstration. A finding is a minimized input that
tokenizes differently across the two implementations, disclosed as a divergence
bug (which stack is "wrong" is for the maintainers). Defect demonstration only.

This harness uses WordPiece (BERT) as the first pairing because slow and fast
BERT tokenizers are both readily constructible from a plain vocab file. Other
pairings (byte-level BPE fast vs slow GPT2, etc.) are natural extensions.
"""

import os
import sys
import tempfile
import warnings

import atheris

warnings.filterwarnings("ignore")

with atheris.instrument_imports():
    from transformers import BertTokenizer, BertTokenizerFast


def _make_pair():
    # A small but non-trivial WordPiece vocab with continuation pieces, so the
    # subword-merging logic (a rich divergence surface) is exercised.
    vocab = [
        "[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]",
        "hello", "world", "foo", "bar", "play", "test", "the", "a", "an",
        "##ing", "##s", "##ed", "##able", "##ly", "##er", "##est", "##ness",
        "un", "re", "pre", "##tion", "##ment", "##ful", "co", "##operate",
        "#", "##", "@", ".", ",", "!", "?",
    ]
    d = tempfile.mkdtemp()
    vp = os.path.join(d, "vocab.txt")
    with open(vp, "w", encoding="utf-8") as f:
        f.write("\n".join(vocab) + "\n")
    slow = BertTokenizer(vocab_file=vp)
    fast = BertTokenizerFast(vocab_file=vp)
    return slow, fast


_SLOW, _FAST = _make_pair()


def _encode_both(text):
    try:
        s = _SLOW.encode(text)
    except Exception:
        s = ("EXC",)
    try:
        f = _FAST.encode(text)
    except Exception:
        f = ("EXC",)
    return s, f


def TestOneInput(data: bytes) -> None:
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        return
    if not text:
        return
    s, f = _encode_both(text)
    # Agreement (same ids, or both raised) is fine. Divergence is the finding.
    if s != f:
        # Raise so the fuzzer records the divergence as a crash artifact; the
        # message carries both tokenizations for triage.
        raise AssertionError(
            f"TOKENIZER DIVERGENCE\n  input={text!r}\n  slow={s}\n  fast={f}"
        )


def _selftest() -> int:
    probes = ["hello world", "playing", "unable", "co##operate", "un-re-pre",
              "hello  world", "\u200b", "  ", "test.", "foo!bar?", "###",
              "hello\x00world", "\uFF21\uFF22", "reﬁne", "a" * 200]
    div = 0
    for p in probes:
        s, f = _encode_both(p)
        if s != f:
            div += 1
            print(f"  DIVERGE input={p!r}\n    slow={s}\n    fast={f}")
    print(f"selftest: {len(probes) - div}/{len(probes)} agree, {div} diverge")
    if div == 0:
        print("baseline invariant holds (fast==slow on probes); oracle is trustworthy")
    else:
        print("NOTE: probe-level divergence found; inspect above before fuzzing")
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

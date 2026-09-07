"""Compare a small BERT WordPiece pairing for correctness observations.

Token-id or exception-type disagreement is a candidate for manual review, not
proof of a vulnerability or universal fast/slow equivalence. Self-test probes
qualify this pairing only. See the target README for historical limitations.
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
    d = tempfile.TemporaryDirectory()
    vp = os.path.join(d.name, "vocab.txt")
    with open(vp, "w", encoding="utf-8") as f:
        f.write("\n".join(vocab) + "\n")
    slow = BertTokenizer(vocab_file=vp)
    fast = BertTokenizerFast(vocab_file=vp)
    d.cleanup()
    return slow, fast


_SLOW, _FAST = _make_pair()


def _encode_both(text):
    try:
        s = _SLOW.encode(text)
    except Exception as exc:
        s = ("EXC", type(exc).__module__, type(exc).__qualname__)
    try:
        f = _FAST.encode(text)
    except Exception as exc:
        f = ("EXC", type(exc).__module__, type(exc).__qualname__)
    return s, f


def TestOneInput(data: bytes) -> None:
    # Total, mutation-preserving mapping. UTF-8 handles ordinary text; Latin-1
    # retains every byte when it is invalid UTF-8, rather than dropping mutations.
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
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
        if s != f or isinstance(s, tuple) or isinstance(f, tuple):
            div += 1
            print(f"  BASELINE FAILURE input={p!r}\n    slow={s}\n    fast={f}")
    print(f"selftest: {len(probes) - div}/{len(probes)} accepted and agree, {div} failed")
    if div == 0:
        print("fast==slow on these probes only; broader equivalence is unproven")
    else:
        print("NOTE: probe-level divergence found; inspect above before fuzzing")
    return 1 if div else 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

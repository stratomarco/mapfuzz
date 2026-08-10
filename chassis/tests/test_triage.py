"""Tests for mapfuzz triage, using fault reports captured from real runs.

Run: python3 -m chassis.tests.test_triage   (or: python3 chassis/tests/test_triage.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from chassis.triage import parse_report, classify, dedup, _iter_inputs  # noqa: E402

FIX = Path(__file__).parent / "fixtures"


def _sig(name):
    return parse_report((FIX / name).read_text())


def test_dedup_collapses_by_location():
    buckets, unparsed = dedup(_iter_inputs([str(FIX)]))
    by_key = {b.signature.key(): b for b in buckets}
    # two FPE reports at gguf.cpp:685 with different addresses -> one bucket
    assert by_key["asan-fpe@gguf.cpp:685"].count == 2
    # two enum-cast reports at :575 with different scrubbed values -> one bucket
    assert by_key["ubsan-invalid-enum@gguf.cpp:575"].count == 2
    assert not unparsed, f"unexpected unparsed: {unparsed}"


def test_classification_matches_session_judgments():
    # enum cast and assertion are shallow blockers (block-and-continue)
    assert classify(_sig("gguf_ubsan_enum_705.txt"))[0] == "shallow"
    assert classify(_sig("gguf_assert_194.txt"))[0] == "shallow"
    # the tokenizers decoder panic is the real finding (0002)
    s = _sig("tokenizers_panic_90.txt")
    assert s.fault_class == "rust-panic-unwrap"
    assert s.location == "mod.rs:90"
    assert classify(s)[0] == "real"
    # memory corruption and native signal are real
    assert classify(_sig("synthetic_heap_overflow.txt"))[0] == "real"
    assert classify(_sig("pytorch_segfault.txt"))[0] == "real"
    # the div-by-zero FPE is review (real DoS but check prior art; ours was a dup)
    assert classify(_sig("gguf_fpe_1.txt"))[0] == "review"


def test_location_and_class_extraction():
    s = _sig("gguf_fpe_1.txt")
    assert s.fault_class == "asan-fpe"
    assert s.location == "gguf.cpp:685"
    assert s.function.startswith("gguf_init_from_reader")
    e = _sig("gguf_ubsan_enum_575_a.txt")
    assert e.fault_class == "ubsan-invalid-enum"
    assert e.location == "gguf.cpp:575"


def _run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())

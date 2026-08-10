"""mapfuzz triage: dedup crash reports by fault location and classify them.

This codifies the manual triage done repeatedly during development: collapse a
pile of crash artifacts into the few DISTINCT faults they represent (by fault
signature, not by input), and tag each as a likely shallow blocker versus a
likely real finding, so attention goes to the right place.

It parses fault-report TEXT, so it is target- and language-agnostic. It handles
the report formats this project produces: AddressSanitizer, UndefinedBehavior-
Sanitizer, Rust panics, Python tracebacks, ggml/GGML_ASSERT aborts, and bare
signals. Feed it report text (from files, a directory of `.txt` reports, or
stdin); pair it with a per-target driver that runs each artifact if you have raw
inputs rather than logs.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# --- canonical signature ------------------------------------------------------
@dataclass(frozen=True)
class Signature:
    fault_class: str        # normalized fault kind, e.g. "asan-heap-overflow"
    location: str           # basename:line (or "unknown")
    function: str = ""      # crashing function if known
    detail: str = ""        # normalized message fragment (values scrubbed)

    def key(self) -> str:
        return f"{self.fault_class}@{self.location}"


# --- normalization helpers ----------------------------------------------------
_HEX = re.compile(r"0x[0-9a-fA-F]+")
_NUM = re.compile(r"\b\d{2,}\b")            # scrub multi-digit varying values
_PATH = re.compile(r"(/[^\s:]+/)+")          # strip directory prefixes


def _basename_line(path_line: str) -> str:
    # ".../ggml/src/gguf.cpp:685:34" -> "gguf.cpp:685"
    s = _PATH.sub("", path_line.strip())
    m = re.match(r"([^\s:]+:\d+)", s)
    return m.group(1) if m else s


def _scrub(msg: str) -> str:
    msg = _HEX.sub("0xADDR", msg)
    msg = _NUM.sub("N", msg)
    return msg.strip()


# --- parsers: return a Signature or None --------------------------------------
def _parse_ubsan(text: str):
    # ".../gguf.cpp:575:17: runtime error: load of value 249, which is not a
    #  valid value for type 'gguf_type'"
    m = re.search(r"([^\s]+:\d+):\d+: runtime error: (.+)", text)
    if not m:
        return None
    loc = _basename_line(m.group(1))
    msg = m.group(2)
    if "not a valid value for type" in msg:
        cls = "ubsan-invalid-enum"
    elif "signed integer overflow" in msg or "cannot be represented" in msg:
        cls = "ubsan-int-overflow"
    elif "division by zero" in msg:
        cls = "ubsan-div-zero"
    elif "out of bounds" in msg or "index" in msg:
        cls = "ubsan-oob-index"
    else:
        cls = "ubsan-other"
    return Signature(cls, loc, detail=_scrub(msg))


def _parse_asan(text: str):
    # "SUMMARY: AddressSanitizer: heap-buffer-overflow /path/f.cc:12 in func"
    # "SUMMARY: AddressSanitizer: FPE /path/gguf.cpp:685:34 in gguf_init..."
    m = re.search(r"AddressSanitizer:\s*([a-zA-Z0-9\-]+)\s+([^\s]+:\d+)(?::\d+)?\s+in\s+([^\s(]+)", text)
    if not m:
        m = re.search(r"AddressSanitizer:\s*([a-zA-Z0-9\-]+)", text)
        if not m:
            return None
        return Signature(f"asan-{m.group(1).lower()}", "unknown")
    kind, loc, func = m.group(1), m.group(2), m.group(3)
    return Signature(f"asan-{kind.lower()}", _basename_line(loc), function=func)


def _parse_ggml_assert(text: str):
    # ".../gguf.cpp:194: GGML_ASSERT(type_to_gguf_type<T>::value == type) failed"
    m = re.search(r"([^\s]+:\d+):\s*GGML_ASSERT\((.+?)\)\s*failed", text)
    if not m:
        return None
    return Signature("assertion-abort", _basename_line(m.group(1)),
                     detail=_scrub(m.group(2)))


def _parse_rust_panic(text: str):
    # "thread '<unnamed>' (id) panicked at /path/decoders/mod.rs:90:63:"
    m = re.search(r"panicked at ([^\s]+:\d+)(?::\d+)?", text)
    if not m:
        return None
    loc = _basename_line(m.group(1))
    # try to grab the panic message on the next non-empty line
    detail = ""
    tail = text[m.end():].splitlines()
    for line in tail:
        if line.strip():
            detail = _scrub(line)
            break
    low = (detail + text).lower()
    if "unwrap" in low or "expect" in low or "called `option::unwrap`" in low:
        cls = "rust-panic-unwrap"
    elif "index out of bounds" in low or "slice" in low:
        cls = "rust-panic-index"
    elif "overflow" in low:
        cls = "rust-panic-overflow"
    else:
        cls = "rust-panic"
    return Signature(cls, loc, detail=detail)


def _parse_python_traceback(text: str):
    # Standard Python traceback: last "File ..., line N, in func" + final
    # "ExcType: message".
    frames = re.findall(r'File "([^"]+)", line (\d+), in (\S+)', text)
    exc = re.search(r"^([A-Za-z_][A-Za-z0-9_.]*Error|Exception|RecursionError):(.*)$",
                    text, re.MULTILINE)
    if not frames and not exc:
        return None
    loc = "unknown"
    func = ""
    if frames:
        f, ln, fn = frames[-1]
        loc = f"{Path(f).name}:{ln}"
        func = fn
    cls = "py-exception"
    if exc:
        etype = exc.group(1)
        if etype == "RecursionError":
            cls = "py-recursion"
        elif etype in ("MemoryError",):
            cls = "py-memory"
        else:
            cls = f"py-{etype.lower()}"
    return Signature(cls, loc, function=func,
                     detail=_scrub(exc.group(2)) if exc else "")


def _parse_bare_signal(text: str):
    if re.search(r"SIGSEGV|Segmentation fault|deadly signal|SIGABRT", text):
        # generic native crash with no better parse; low confidence location
        return Signature("native-signal", "unknown")
    return None


# Order matters: most specific first.
_PARSERS = (
    _parse_ubsan,
    _parse_asan,
    _parse_ggml_assert,
    _parse_rust_panic,
    _parse_python_traceback,
    _parse_bare_signal,
)


def parse_report(text: str):
    """Return the best Signature for a fault report, or None if unrecognized."""
    for p in _PARSERS:
        sig = p(text)
        if sig is not None:
            return sig
    return None


# --- classification: shallow-blocker vs likely-real ---------------------------
# Derived from what this project actually saw. "shallow" means: known-cheap fault
# that walls the fuzzer; block it locally to go deeper. "real" means: worth
# triaging as a finding. "review" means: cannot decide from the signature alone.
_VERDICT = {
    "ubsan-invalid-enum": ("shallow", "unvalidated enum cast; guard at the reader"),
    "assertion-abort": ("shallow", "assertion reachable from input; DoS, often intended"),
    "ubsan-div-zero": ("review", "div-by-zero: real DoS but frequently already known"),
    "asan-fpe": ("review", "arithmetic fault (div-by-zero); real DoS, check prior art"),
    "ubsan-int-overflow": ("review", "integer overflow; may or may not be exploitable"),
    "rust-panic-unwrap": ("real", "unwrap/expect on untrusted input; DoS finding"),
    "rust-panic-index": ("real", "index/slice panic on untrusted input; DoS finding"),
    "rust-panic-overflow": ("review", "arithmetic panic; check whether input-driven"),
    "rust-panic": ("review", "panic on untrusted input; inspect message"),
    "py-recursion": ("review", "recursion/stack exhaustion; DoS"),
    "native-signal": ("real", "native crash (possible memory corruption); inspect"),
}
# ASan memory-corruption family is always real.
_ASAN_REAL_PREFIXES = ("asan-heap", "asan-stack", "asan-global",
                       "asan-use-after", "asan-double-free")


def classify(sig: Signature):
    """Return (verdict, reason) where verdict in {real, shallow, review}."""
    fc = sig.fault_class
    if any(fc.startswith(p) for p in _ASAN_REAL_PREFIXES):
        return ("real", "AddressSanitizer memory-safety violation")
    if fc in _VERDICT:
        return _VERDICT[fc]
    if fc.startswith("py-") and fc not in ("py-recursion",):
        return ("review", "python exception; distinguish clean rejection from bug")
    return ("review", "unclassified; inspect manually")


# --- dedup + report -----------------------------------------------------------
@dataclass
class Bucket:
    signature: Signature
    count: int = 0
    sources: list = field(default_factory=list)   # filenames/ids


def dedup(reports):
    """reports: iterable of (source_id, text). Returns buckets sorted by count."""
    buckets: dict[str, Bucket] = {}
    unparsed = []
    for source_id, text in reports:
        sig = parse_report(text)
        if sig is None:
            unparsed.append(source_id)
            continue
        b = buckets.setdefault(sig.key(), Bucket(sig))
        b.count += 1
        if len(b.sources) < 3:
            b.sources.append(source_id)
    ordered = sorted(buckets.values(), key=lambda b: b.count, reverse=True)
    return ordered, unparsed


def format_table(buckets, unparsed):
    lines = []
    lines.append(f"{'count':>6}  {'verdict':<8} {'class':<22} {'location':<24} example")
    lines.append("-" * 90)
    for b in buckets:
        verdict, _reason = classify(b.signature)
        ex = b.sources[0] if b.sources else ""
        lines.append(f"{b.count:>6}  {verdict:<8} {b.signature.fault_class:<22} "
                     f"{b.signature.location:<24} {ex}")
    if unparsed:
        lines.append("")
        lines.append(f"unparsed reports: {len(unparsed)} (e.g. {unparsed[:2]})")
    return "\n".join(lines)


def _iter_inputs(argv):
    paths = [a for a in argv if not a.startswith("-")]
    if not paths:
        yield ("<stdin>", sys.stdin.read())
        return
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.glob("*")):
                if f.is_file():
                    yield (f.name, f.read_text(errors="replace"))
        elif path.is_file():
            yield (path.name, path.read_text(errors="replace"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    buckets, unparsed = dedup(_iter_inputs(argv))
    print(format_table(buckets, unparsed))
    # exit non-zero if any 'real' bucket exists, so CI can gate on it
    return 1 if any(classify(b.signature)[0] == "real" for b in buckets) else 0


if __name__ == "__main__":
    raise SystemExit(main())

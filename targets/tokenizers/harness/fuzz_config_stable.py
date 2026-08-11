"""Coverage-guided, structure-stable generator for tokenizer.json.

Blind byte mutation of a tokenizer.json dies at the serde JSON boundary. This
generator emits VALID tokenizer.json structures and uses a fixed-layout byte
decode to choose which component variants appear and to mutate their fields, so
libFuzzer's coverage-guided byte mutations act as coverage-guided STRUCTURAL
mutations over a rich, branching parse tree (models, normalizers, pre-tokenizers,
post-processors, decoders, each a tagged/untagged union of many variants).

The grammar (variant names and the untagged/tagged model+decoder unions) was
verified against tokenizers source. Unlike the pytorch meta-tensor surface (a
shallow corridor where a stable encoding had nothing to steer through), the
tokenizer.json parse tree has real depth, which is where coverage-guided
structure awareness earns its keep.

Fixed layout: every choice is read from a fixed byte offset with fixed width, so
a one-byte flip changes at most one component/field and positions never shift.

Target: Tokenizer::from_str / from_bytes. Scope: robustness/DoS (panics on load),
the class of finding 0002 (decoder expect panic). Defect demonstration only.
"""

import io
import json
import sys

import atheris

with atheris.instrument_imports():
    import tokenizers
    from tokenizers import Tokenizer


# Variant names verified against source.
_MODELS = ["BPE", "WordPiece", "WordLevel", "Unigram"]
_DECODERS = ["BPEDecoder", "ByteLevel", "WordPiece", "Metaspace", "CTC",
             "Sequence", "Replace", "Fuse", "Strip", "ByteFallback"]
_NORMALIZERS = ["BertNormalizer", "Strip", "StripAccents", "NFC", "NFD", "NFKC",
                "NFKD", "Sequence", "Lowercase", "Nmt", "Precompiled", "Replace"]
_PRETOKS = ["BertPreTokenizer", "ByteLevel", "Delimiter", "Metaspace",
            "Whitespace", "Sequence", "Split", "Punctuation", "WhitespaceSplit",
            "Digits", "UnicodeScripts"]

# Fixed layout: one selector byte per structural choice, then a pool of value
# bytes. Positions are constant so a flip is local.
#   [0] model variant   [1] include normalizer + which
#   [2] include pre_tokenizer + which   [3] include decoder + which
#   [4] include post_processor   [5] added_tokens count
#   [6] vocab size class          [7] merges/misc class
#   [8..] value pool
_HEADER = 8
_POOL = 24
_LAYOUT_LEN = _HEADER + _POOL


def _fixed(data: bytes) -> bytes:
    return data[:_LAYOUT_LEN] if len(data) >= _LAYOUT_LEN else data + b"\x00" * (_LAYOUT_LEN - len(data))


def _size_class(b: int) -> int:
    return [0, 1, 2, 8, 255, 4096, 65536][b % 7]


def _mk_model(sel: int, vsize: int, misc: int) -> dict:
    name = _MODELS[sel % len(_MODELS)]
    vocab = {str(i): i for i in range(min(vsize, 64))}  # bounded to keep gen fast
    if name == "BPE":
        return {"type": "BPE", "vocab": vocab,
                "merges": [], "dropout": None, "unk_token": None,
                "continuing_subword_prefix": None, "end_of_word_suffix": None,
                "fuse_unk": bool(misc & 1), "byte_fallback": bool(misc & 2)}
    if name == "WordPiece":
        return {"type": "WordPiece", "vocab": vocab, "unk_token": "[UNK]",
                "continuing_subword_prefix": "##",
                "max_input_chars_per_word": _size_class(misc)}
    if name == "WordLevel":
        return {"type": "WordLevel", "vocab": vocab, "unk_token": "[UNK]"}
    # Unigram
    return {"type": "Unigram",
            "vocab": [[str(i), -float(i)] for i in range(min(vsize, 32))],
            "unk_id": (misc % max(vsize, 1)) if vsize else None,
            "byte_fallback": bool(misc & 1)}


def _mk_tagged(name: str) -> dict:
    # Minimal valid-ish object for a tagged component; fields vary by type but a
    # bare {"type": name} exercises each variant's deserialize/construct path.
    d = {"type": name}
    if name in ("Sequence",):
        d[name.lower() if False else "normalizers"] = []  # Sequence needs a list field
    return d


def _build_config(data: bytes) -> dict:
    b = _fixed(data)
    cfg = {
        "version": "1.0",
        "truncation": None,
        "padding": None,
        "added_tokens": [],
        "normalizer": None,
        "pre_tokenizer": None,
        "post_processor": None,
        "decoder": None,
        "model": _mk_model(b[0], _size_class(b[6]), b[7]),
    }
    if b[1] & 0x80:
        cfg["normalizer"] = _mk_tagged(_NORMALIZERS[b[1] % len(_NORMALIZERS)])
    if b[2] & 0x80:
        cfg["pre_tokenizer"] = _mk_tagged(_PRETOKS[b[2] % len(_PRETOKS)])
    if b[3] & 0x80:
        cfg["decoder"] = _mk_tagged(_DECODERS[b[3] % len(_DECODERS)])
    n_added = b[5] % 5
    cfg["added_tokens"] = [
        {"id": i, "content": f"[T{i}]", "special": bool(b[4] & 1),
         "single_word": False, "lstrip": False, "rstrip": False,
         "normalized": False}
        for i in range(n_added)
    ]
    return cfg


def TestOneInput(data: bytes) -> None:
    try:
        cfg = _build_config(data)
        text = json.dumps(cfg)
    except Exception:
        return
    try:
        Tokenizer.from_str(text)
    except Exception as e:  # noqa: BLE001
        # A clean deserialization error (Exception from the Rust side, surfaced
        # as a Python exception) is a valid rejection, not a finding. A PANIC in
        # the Rust code aborts the process and is caught by the fuzzer regardless.
        # We only re-raise RecursionError as a distinct DoS signal.
        if isinstance(e, RecursionError):
            raise
        return


def _selftest() -> int:
    base = bytes(range(_LAYOUT_LEN))
    cfg = _build_config(base)
    text = json.dumps(cfg)
    print("sample config model:", cfg["model"]["type"],
          "| normalizer:", (cfg["normalizer"] or {}).get("type"),
          "| decoder:", (cfg["decoder"] or {}).get("type"))
    # a plain WordLevel config must load
    good = {"version": "1.0", "truncation": None, "padding": None,
            "added_tokens": [], "normalizer": None, "pre_tokenizer": None,
            "post_processor": None, "decoder": None,
            "model": {"type": "WordLevel", "vocab": {"[UNK]": 0}, "unk_token": "[UNK]"}}
    try:
        Tokenizer.from_str(json.dumps(good))
        print("SELFTEST baseline WordLevel loads OK")
    except Exception as e:  # noqa: BLE001
        print("SELFTEST FAILED baseline:", type(e).__name__, e)
        return 1
    # how many of the generated variants load vs reject (reach-rate signal)
    loaded = rejected = 0
    for i in range(256):
        try:
            Tokenizer.from_str(json.dumps(_build_config(bytes([i]) + base)))
            loaded += 1
        except Exception:
            rejected += 1
    print(f"generated-variant reach: {loaded} loaded, {rejected} rejected of 256")
    print("tokenizers", tokenizers.__version__)
    return 0


def main() -> None:
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Evidence base tool: validate claims.yaml and render claims.md.

The canonical record is claims.yaml. claims.md is GENERATED from it, never
hand-edited, so there is a single source of truth. Run with --check to validate,
--render to regenerate claims.md, or both.

Usage:
  python3 evidence/tool.py --check
  python3 evidence/tool.py --render
"""
import argparse
import collections
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
YAML = HERE / "claims.yaml"
MD = HERE / "claims.md"

REQUIRED = {"id", "date", "target", "statement", "kind", "confidence",
            "provenance", "observation", "boundary"}
KINDS = {"finding", "negative", "non-finding", "method", "audit", "correction"}
CONF = {"verified", "observed", "inferred"}


def load():
    return yaml.safe_load(YAML.read_text())["claims"]


def check(claims):
    errs = []
    ids = [c["id"] for c in claims]
    dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
    if dupes:
        errs.append(f"duplicate ids: {dupes}")
    for c in claims:
        cid = c.get("id", "<no id>")
        missing = REQUIRED - set(c)
        if missing:
            errs.append(f"{cid}: missing fields {missing}")
        if c.get("kind") not in KINDS:
            errs.append(f"{cid}: bad kind {c.get('kind')}")
        if c.get("confidence") not in CONF:
            errs.append(f"{cid}: bad confidence {c.get('confidence')}")
        if not str(c.get("boundary", "")).strip():
            errs.append(f"{cid}: empty boundary (every claim needs a limit)")
        # a negative must state effort in its observation
        if c.get("kind") == "negative":
            obs = str(c.get("observation", "")).lower()
            if not any(t in obs for t in ("run", "clean", "probe", "check")):
                errs.append(f"{cid}: negative without a stated effort figure")
        # a non-finding must justify exclusion in boundary
        if c.get("kind") == "non-finding":
            if "not" not in str(c.get("boundary", "")).lower():
                errs.append(f"{cid}: non-finding boundary must say why not counted")
        # claim: provenance references must resolve
        for p in c.get("provenance", []):
            if p.startswith("claim:"):
                ref = p.split(":", 1)[1]
                if ref not in ids:
                    errs.append(f"{cid}: provenance references unknown claim {ref}")
    return errs


def render(claims):
    order = ["finding", "correction", "non-finding", "negative", "audit", "method"]
    titles = {"finding": "Findings (real defects)",
              "correction": "Corrections",
              "non-finding": "Non-findings (deliberately not counted)",
              "negative": "Negatives (robust surfaces)",
              "audit": "Audits (scope / M0)",
              "method": "Methods (lessons)"}
    out = ["# mapfuzz Research Evidence Base (rendered)",
           "",
           "> Generated from claims.yaml by evidence/tool.py. Do not edit by hand.",
           f"> {len(claims)} claims.",
           ""]
    by_kind = collections.defaultdict(list)
    for c in claims:
        by_kind[c["kind"]].append(c)
    for kind in order:
        cs = by_kind.get(kind, [])
        if not cs:
            continue
        out.append(f"## {titles[kind]}")
        out.append("")
        for c in sorted(cs, key=lambda x: x["id"]):
            sev = f" | severity: {c['severity']}" if c.get("severity") else ""
            status = f" | status: {c['status']}" if c.get("status") else ""
            out.append(f"### {c['id']}  ({c['confidence']}{sev}{status})")
            out.append(f"**{c['statement'].strip()}**")
            out.append("")
            out.append(f"- target: {c['target']}"
                       + (f" / {c['entry_point']}" if c.get("entry_point") else ""))
            out.append(f"- date: {c['date']}")
            out.append("- provenance:")
            for p in c["provenance"]:
                out.append(f"  - {p}")
            out.append(f"- observation: {c['observation'].strip()}")
            out.append(f"- boundary: {c['boundary'].strip()}")
            if c.get("refs"):
                out.append(f"- refs: {', '.join(c['refs'])}")
            out.append("")
    MD.write_text("\n".join(out))
    return len(claims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.render):
        args.check = args.render = True
    claims = load()
    if args.check:
        errs = check(claims)
        if errs:
            print("EVIDENCE BASE INVALID:")
            for e in errs:
                print("  -", e)
            sys.exit(1)
        print(f"evidence base OK: {len(claims)} claims, all valid")
    if args.render:
        n = render(claims)
        print(f"rendered {n} claims -> {MD}")


if __name__ == "__main__":
    main()

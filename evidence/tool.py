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
import datetime
import re
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
SEVERITIES = {"high", "medium", "medium-low", "low", "none"}
TAGS = {"source-read", "sandbox-run", "machine-run", "execution-run", "environment", "claim"}
ID = re.compile(r"C-[0-9]{4}\Z")


class ClaimLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than silently replacing evidence."""


def _mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError(f"invalid or duplicate mapping key at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node)
    return result


ClaimLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load(path=YAML):
    doc = yaml.load(path.read_text(encoding="utf-8"), Loader=ClaimLoader)
    if not isinstance(doc, dict) or set(doc) != {"claims"}:
        raise ValueError("document must contain only a claims list")
    return doc["claims"]


def check(claims):
    errs = []
    if not isinstance(claims, list) or not claims:
        return ["claims must be a nonempty list"]
    ids = [c["id"] for c in claims if isinstance(c, dict) and isinstance(c.get("id"), str)]
    dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
    if dupes:
        errs.append(f"duplicate ids: {dupes}")
    for index, c in enumerate(claims):
        if not isinstance(c, dict):
            errs.append(f"record {index}: expected a mapping")
            continue
        cid = c.get("id", "<no id>")
        missing = REQUIRED - set(c)
        if missing:
            errs.append(f"{cid}: missing fields {missing}")
        unknown = set(c) - REQUIRED - {"entry_point", "severity", "status", "refs"}
        if unknown:
            errs.append(f"{cid}: unknown fields {sorted(map(str, unknown))}")
        if not isinstance(cid, str) or not ID.fullmatch(cid):
            errs.append(f"record {index}: id must match C-NNNN")
        for field in ("target", "statement", "observation", "boundary", "entry_point"):
            if field == "entry_point" and field not in c:
                continue
            if not isinstance(c.get(field), str) or not c[field].strip():
                errs.append(f"{cid}: {field} must be a nonempty string")
        date = c.get("date")
        try:
            if type(date) is datetime.date:
                pass
            elif isinstance(date, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date):
                datetime.date.fromisoformat(date)
            else:
                raise ValueError()
        except ValueError:
            errs.append(f"{cid}: date must be a valid YYYY-MM-DD date")
        if not isinstance(c.get("kind"), str) or c["kind"] not in KINDS:
            errs.append(f"{cid}: bad kind {c.get('kind')}")
        if not isinstance(c.get("confidence"), str) or c["confidence"] not in CONF:
            errs.append(f"{cid}: bad confidence {c.get('confidence')}")
        if c.get("kind") == "finding" and c.get("confidence") not in ("verified", "observed"):
            errs.append(f"{cid}: finding must be verified or observed")
        if "severity" in c and (not isinstance(c["severity"], str) or c["severity"] not in SEVERITIES):
            errs.append(f"{cid}: invalid severity")
        if c.get("kind") not in ("finding", "non-finding") and "severity" in c:
            errs.append(f"{cid}: omit severity outside findings/non-findings")
        status = c.get("status", "active")
        if not isinstance(status, str):
            errs.append(f"{cid}: status must be a string")
        elif status.startswith("superseded:"):
            ref = status.partition(":")[2]
            if ref not in ids or ref == cid:
                errs.append(f"{cid}: invalid superseded reference {ref}")
        elif status not in {"active", "embargoed", "reported"}:
            errs.append(f"{cid}: invalid status {status}")
        if "refs" in c and (not isinstance(c["refs"], list) or any(not isinstance(r, str) or not r.strip() for r in c["refs"])):
            errs.append(f"{cid}: refs must be a list of nonempty strings")
        provenance = c.get("provenance")
        if not isinstance(provenance, list) or not provenance:
            errs.append(f"{cid}: provenance must be a nonempty list")
            continue
        # claim: provenance references must resolve
        for p in provenance:
            if not isinstance(p, str):
                errs.append(f"{cid}: provenance entries must be strings")
                continue
            tag, sep, detail = p.partition(":")
            if tag not in TAGS or not sep or not detail.strip():
                errs.append(f"{cid}: invalid provenance tag/detail: {p}")
            if tag == "claim":
                ref = detail
                if ref not in ids or ref == cid:
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
    MD.write_text("\n".join(out), encoding="utf-8")
    return len(claims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--render", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.render):
        args.check = args.render = True
    try:
        claims = load()
        errs = check(claims)
    except (ValueError, yaml.YAMLError, OSError) as e:
        errs = [str(e)]
    if errs:
        print("EVIDENCE BASE INVALID:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print(f"schema checks passed: {len(claims)} claims; truth and semantic scope require human review")
    if args.render:
        n = render(claims)
        print(f"rendered {n} claims -> {MD}")


if __name__ == "__main__":
    main()

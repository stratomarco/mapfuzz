import copy
import tempfile
import unittest
from pathlib import Path

from evidence.tool import check, load


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.claim = dict(id="C-0001", date="2026-09-07", target="fixture",
                          statement="A bounded fixture.", kind="finding",
                          confidence="observed", provenance=["sandbox-run:fixture"],
                          observation="One test.", boundary="Synthetic only.")

    def test_valid(self):
        self.assertEqual(check([self.claim]), [])

    def test_malformed_fields(self):
        cases = {"id": [None, [], "C-1", "X-0001"],
                 "date": ["2026-02-30", "2026-9-7", 123, None],
                 "kind": [[], "wrong"], "confidence": [{}, "inferred"],
                 "statement": ["", " ", [], None], "boundary": [None, ""],
                 "observation": [[], ""], "target": [1, ""],
                 "provenance": [[], None, "source-read:a", [{}], ["web:a"], ["source-read:"], ["claim"]],
                 "status": [[], "done", "superseded:C-9999", "superseded:C-0001"],
                 "severity": [[], "critical"], "refs": ["a", [None]]}
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    claim = copy.deepcopy(self.claim)
                    claim[field] = value
                    self.assertTrue(check([claim]))

    def test_missing_fields_and_wrong_containers(self):
        for field in self.claim:
            claim = self.claim.copy()
            del claim[field]
            self.assertTrue(check([claim]), field)
        for value in (None, {}, [], [None], [42], [[]]):
            self.assertTrue(check(value))

    def test_references_duplicates_and_unknown_fields(self):
        self.assertTrue(check([self.claim, self.claim]))
        for ref in ("claim:C-9999", "claim:C-0001"):
            self.assertTrue(check([dict(self.claim, provenance=[ref])]))
        self.assertTrue(check([dict(self.claim, typo="x")]))
        self.assertTrue(check([dict(self.claim, kind="audit", severity="none")]))
        second = dict(self.claim, id="C-0002", provenance=["claim:C-0001"])
        self.assertEqual(check([self.claim, second]), [])

    def test_duplicate_yaml_keys_and_bad_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claims.yaml"
            for text in ("claims: []\nclaims: []", "claims:\n- id: C-0001\n  id: C-0002", "[]", "null", "claims: []\nextra: 1"):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load(path)


if __name__ == "__main__":
    unittest.main()

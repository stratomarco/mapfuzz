import copy
from pathlib import Path
import tempfile
import unittest

import yaml

from chassis.qualification_manifest import MANIFEST, ROOT, validate_manifest


class QualificationManifestTests(unittest.TestCase):
    def setUp(self):
        self.document = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    def validate_copy(self, document):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "qualification.yaml"
            path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
            return validate_manifest(path=path, root=ROOT)

    def test_repository_manifest(self):
        document = validate_manifest()
        self.assertEqual(len(document["targets"]), 9)

    def test_rejects_lifecycle_compute_mismatch(self):
        document = copy.deepcopy(self.document)
        document["targets"][0]["compute_decision"] = "m0-only"
        with self.assertRaisesRegex(ValueError, "requires compute_decision parked"):
            self.validate_copy(document)

    def test_rejects_duplicate_target(self):
        document = copy.deepcopy(self.document)
        document["targets"].append(copy.deepcopy(document["targets"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate target id"):
            self.validate_copy(document)

    def test_rejects_duplicate_yaml_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "qualification.yaml"
            path.write_text("schema_version: 1\nschema_version: 1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate YAML key"):
                validate_manifest(path=path, root=ROOT)

    def test_rejects_missing_evidence(self):
        document = copy.deepcopy(self.document)
        document["targets"][0]["evidence"] = ["docs/does-not-exist.md"]
        with self.assertRaisesRegex(ValueError, "missing evidence path"):
            self.validate_copy(document)

    def test_rejects_looser_or_boolean_cap(self):
        for value in (2, True):
            with self.subTest(value=value):
                document = copy.deepcopy(self.document)
                document["qualification_contract"]["caps"]["cpu_workers"] = value
                with self.assertRaisesRegex(ValueError, "cpu_workers"):
                    self.validate_copy(document)

    def test_rejects_future_m0(self):
        document = copy.deepcopy(self.document)
        document["targets"][0]["last_m0"] = "2999-01-01"
        with self.assertRaisesRegex(ValueError, "cannot be in the future"):
            self.validate_copy(document)

    def test_rejects_changed_stop_contract(self):
        document = copy.deepcopy(self.document)
        document["qualification_contract"]["stop_rules"] = ["run forever"]
        with self.assertRaisesRegex(ValueError, "must match the reviewed contract"):
            self.validate_copy(document)

    def test_rejects_noncanonical_evidence_paths(self):
        for path in ("/etc/hosts", "docs/../docs/TARGETS.md", r"docs\TARGETS.md"):
            with self.subTest(path=path):
                document = copy.deepcopy(self.document)
                document["targets"][0]["evidence"] = [path]
                with self.assertRaisesRegex(ValueError, "canonical and repository-relative"):
                    self.validate_copy(document)


if __name__ == "__main__":
    unittest.main()

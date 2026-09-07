import json
import os
import unittest

from chassis.resource_oracle import OK, REJECTED, run_capped, assert_guards_class


def ignore(data):
    pass


def die(data):
    os._exit(9)


def silent_exit(data):
    os._exit(0)


def long_error(data):
    raise ValueError("x" * 100000)


class ResourceTests(unittest.TestCase):
    def test_normal_return_requires_explicit_policy(self):
        self.assertTrue(assert_guards_class(ignore, b"bomb", b"good"))
        self.assertEqual(assert_guards_class(ignore, b"bomb", b"good", allow_bomb_ok=True), [])

    def test_unexplained_death_is_not_oom(self):
        for loader in (die, silent_exit):
            self.assertEqual(run_capped(loader, b"")[0], "child-error")
            self.assertTrue(assert_guards_class(loader, b"", b""))

    def test_long_exception_does_not_block_ipc(self):
        self.assertEqual(run_capped(long_error, b"")[0], REJECTED)

    def test_real_json_loader(self):
        # Deterministic syntax rejection, independent of recursion thresholds.
        self.assertEqual(run_capped(json.loads, b'{"count":4}')[0], OK)
        for malformed in (b'{"count":', b'[1,]', b'{'):
            with self.subTest(malformed=malformed):
                outcome, detail = run_capped(json.loads, malformed)
                self.assertEqual(outcome, REJECTED)
                self.assertTrue(detail.startswith("JSONDecodeError:"), detail)

    def test_nested_json_stays_within_caps(self):
        # These are valid JSON inputs. Python versions can accept or reject
        # different depths; either is resource-bounded. Do not weaken the
        # separate assert_guards_class hostile-input rejection policy.
        for depth in (2000, 4000, 8000):
            with self.subTest(depth=depth):
                nested = b"[" * depth + b"0" + b"]" * depth
                outcome, detail = run_capped(json.loads, nested)
                self.assertIn(outcome, (OK, REJECTED), (outcome, detail))
                if outcome == REJECTED:
                    self.assertTrue(detail.startswith("RecursionError:"), detail)


if __name__ == "__main__":
    unittest.main()

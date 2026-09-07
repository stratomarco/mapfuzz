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
        # Actual stdlib parser, synthetic nesting family; no third-party safety claim.
        self.assertEqual(run_capped(json.loads, b'{"count":4}')[0], OK)
        for depth in (2000, 4000, 8000):
            bomb = b"[" * depth + b"0" + b"]" * depth
            self.assertEqual(run_capped(json.loads, bomb)[0], REJECTED)


if __name__ == "__main__":
    unittest.main()

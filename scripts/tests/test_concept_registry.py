import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import concept_registry as reg  # noqa: E402


class TestRegisterLookup(unittest.TestCase):
    def test_register_creates_entry_and_lookup_finds_it(self):
        with tempfile.TemporaryDirectory() as root:
            entry = reg.register(root, "quicksort", "Quicksort",
                                 "A sorting algorithm that partitions around a pivot.")
            self.assertEqual(entry["status"], "registered")
            self.assertIsNone(entry["figure"])
            found = reg.lookup(root, "quicksort")
            self.assertEqual(found, entry)
            on_disk = os.path.join(root, "quicksort", "entry.json")
            self.assertTrue(os.path.exists(on_disk))
            with open(on_disk, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["slug"], "quicksort")

    def test_lookup_unknown_returns_none(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(reg.lookup(root, "nope"))

    def test_register_same_definition_is_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            a = reg.register(root, "recursion", "Recursion", "A thing defined using itself.")
            b = reg.register(root, "recursion", "Recursion", "A thing defined using itself.")
            self.assertEqual(a, b)

    def test_register_same_slug_different_definition_raises(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "mean", "Mean", "The average of a set of numbers.")
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "mean", "Mean", "Unkind behaviour.")

    def test_invalid_slug_raises(self):
        with tempfile.TemporaryDirectory() as root:
            for bad in ("Has Space", "CamelCase", "trailing-", "-leading", "под"):
                with self.assertRaises(reg.RegistryError):
                    reg.register(root, bad, "X", "Y.")

    def test_blank_name_or_definition_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "x", "  ", "def.")
            with self.assertRaises(reg.RegistryError):
                reg.register(root, "x", "X", "")

    def test_register_with_prerequisites(self):
        with tempfile.TemporaryDirectory() as root:
            entry = reg.register(root, "rsa-encryption", "RSA encryption",
                                 "Public-key encryption built on modular arithmetic.",
                                 prerequisites=["modular-arithmetic", "prime-numbers"])
            self.assertEqual(entry["prerequisites"],
                             ["modular-arithmetic", "prime-numbers"])


if __name__ == "__main__":
    unittest.main()

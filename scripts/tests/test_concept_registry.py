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


class TestAttachAndIndex(unittest.TestCase):
    def _figure_dir(self, base):
        fig = os.path.join(base, "fig")
        os.makedirs(fig, exist_ok=True)
        with open(os.path.join(fig, "figure.json"), "w", encoding="utf-8") as fh:
            json.dump({"concept_slug": "quicksort"}, fh)
        return fig

    def test_attach_figure_marks_illustrated(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "quicksort", "Quicksort", "Partition sort.")
            fig = self._figure_dir(root)
            entry = reg.attach_figure(root, "quicksort", fig)
            self.assertEqual(entry["status"], "illustrated")
            self.assertTrue(entry["figure"])
            self.assertEqual(reg.lookup(root, "quicksort")["status"], "illustrated")

    def test_attach_to_unknown_slug_raises(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(reg.RegistryError):
                reg.attach_figure(root, "ghost", root)

    def test_attach_without_figure_json_raises(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "x", "X", "def.")
            empty = os.path.join(root, "empty")
            os.makedirs(empty)
            with self.assertRaises(reg.RegistryError):
                reg.attach_figure(root, "x", empty)

    def test_build_index_lists_entries(self):
        with tempfile.TemporaryDirectory() as root:
            reg.register(root, "a-thing", "A thing", "First.")
            reg.register(root, "b-thing", "B thing", "Second.")
            index = reg.build_index(root)
            self.assertEqual(sorted(index), ["a-thing", "b-thing"])
            self.assertEqual(index["a-thing"]["status"], "registered")
            with open(os.path.join(root, "index.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh), index)


class TestCli(unittest.TestCase):
    def test_register_lookup_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            rc = reg.main(["--root", root, "register", "--slug", "recursion",
                           "--name", "Recursion",
                           "--definition", "A thing defined using itself."])
            self.assertEqual(rc, 0)
            self.assertEqual(reg.main(["--root", root, "lookup", "recursion"]), 0)

    def test_lookup_missing_exits_1(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(reg.main(["--root", root, "lookup", "ghost"]), 1)

    def test_collision_exits_1(self):
        with tempfile.TemporaryDirectory() as root:
            reg.main(["--root", root, "register", "--slug", "mean",
                      "--name", "Mean", "--definition", "The average."])
            rc = reg.main(["--root", root, "register", "--slug", "mean",
                           "--name", "Mean", "--definition", "Unkind."])
            self.assertEqual(rc, 1)

    def test_index_command(self):
        with tempfile.TemporaryDirectory() as root:
            reg.main(["--root", root, "register", "--slug", "x",
                      "--name", "X", "--definition", "def."])
            self.assertEqual(reg.main(["--root", root, "index"]), 0)
            self.assertTrue(os.path.exists(os.path.join(root, "index.json")))


class TestRobustness(unittest.TestCase):
    def test_corrupt_entry_json_raises_registry_error(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "broken"))
            with open(os.path.join(root, "broken", "entry.json"), "w") as fh:
                fh.write("{not json")
            with self.assertRaises(reg.RegistryError):
                reg.lookup(root, "broken")

    def test_corrupt_entry_exits_1_via_cli(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "broken"))
            with open(os.path.join(root, "broken", "entry.json"), "w") as fh:
                fh.write("{not json")
            self.assertEqual(reg.main(["--root", root, "lookup", "broken"]), 1)

    def test_partial_entry_in_index_raises_registry_error(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "partial"))
            with open(os.path.join(root, "partial", "entry.json"), "w") as fh:
                json.dump({"slug": "partial"}, fh)
            with self.assertRaises(reg.RegistryError):
                reg.build_index(root)

    def test_attach_figure_relpath_round_trips_outside_root(self):
        with tempfile.TemporaryDirectory() as base:
            root = os.path.join(base, "registry")
            fig = os.path.join(base, "figures", "demo")
            os.makedirs(fig)
            with open(os.path.join(fig, "figure.json"), "w", encoding="utf-8") as fh:
                json.dump({"concept_slug": "demo"}, fh)
            reg.register(root, "demo", "Demo", "A demo.")
            entry = reg.attach_figure(root, "demo", fig)
            resolved = os.path.normpath(os.path.join(root, entry["figure"]))
            self.assertTrue(os.path.exists(os.path.join(resolved, "figure.json")))


class TestSeededRegistry(unittest.TestCase):
    ROOT = os.path.join(SCRIPTS_DIR, os.pardir, "registry")

    def test_quicksort_is_illustrated_and_figure_exists(self):
        entry = reg.lookup(self.ROOT, "quicksort")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "illustrated")
        figure_dir = os.path.normpath(os.path.join(self.ROOT, entry["figure"]))
        self.assertTrue(os.path.exists(os.path.join(figure_dir, "figure.json")))

    def test_modular_arithmetic_is_registered(self):
        entry = reg.lookup(self.ROOT, "modular-arithmetic")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["status"], "registered")

    def test_index_matches_entries(self):
        index = reg.build_index(self.ROOT)
        self.assertIn("quicksort", index)
        self.assertIn("modular-arithmetic", index)


if __name__ == "__main__":
    unittest.main()

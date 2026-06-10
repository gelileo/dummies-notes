import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import assemble as asm  # noqa: E402
import concept_registry as reg  # noqa: E402


def write_decomp(graph_dir, slug, atomic, prereqs=()):
    """prereqs: list of slugs; expands to full prerequisite objects."""
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug.replace("-", " ").title(),
                    "definition": f"Plain definition of {slug}."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "atomic_reason": "fixture.",
        "prerequisites": [
            {"slug": p, "name": p.replace("-", " ").title(),
             "definition": f"Plain definition of {p}.", "why": f"{slug} needs {p}."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


class TestLoadFullGraph(unittest.TestCase):
    def test_loads_names_definitions_and_prereq_objects(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa-encryption", False, ["prime-numbers"])
            nodes, issues = asm.load_full_graph(d)
            self.assertEqual([m for lvl, m in issues if lvl == "ERROR"], [])
            node = nodes["rsa-encryption"]
            self.assertEqual(node["name"], "Rsa Encryption")
            self.assertIn("Plain definition", node["definition"])
            self.assertEqual(node["prerequisites"][0]["slug"], "prime-numbers")
            self.assertIn("why", node["prerequisites"][0])

    def test_missing_dir_errors(self):
        nodes, issues = asm.load_full_graph("/nonexistent")
        self.assertTrue(any(lvl == "ERROR" for lvl, _ in issues))


class TestFindRoot(unittest.TestCase):
    def test_single_root(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["primes", "asym"])
            write_decomp(d, "primes", True)
            write_decomp(d, "asym", True)
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.find_root(nodes), "rsa")

    def test_multiple_roots_raise(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", True)
            write_decomp(d, "b", True)
            nodes, _ = asm.load_full_graph(d)
            with self.assertRaises(ValueError):
                asm.find_root(nodes)


class TestTopoOrder(unittest.TestCase):
    def test_prereqs_come_before_dependents_root_last(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["primes", "asym"])
            write_decomp(d, "primes", True)
            write_decomp(d, "asym", True)
            nodes, _ = asm.load_full_graph(d)
            order = asm.topo_order(nodes)
            self.assertEqual(order[-1], "rsa")
            self.assertLess(order.index("asym"), order.index("rsa"))
            self.assertLess(order.index("primes"), order.index("rsa"))

    def test_deterministic_alphabetical_ties(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "top", False, ["zeta", "alpha"])
            write_decomp(d, "zeta", True)
            write_decomp(d, "alpha", True)
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.topo_order(nodes), ["alpha", "zeta", "top"])

    def test_out_of_graph_prereqs_are_ignored_for_ordering(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "solo", True, ["external-thing"])
            nodes, _ = asm.load_full_graph(d)
            self.assertEqual(asm.topo_order(nodes), ["solo"])

    def test_cycle_raises(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", False, ["a"])
            nodes, _ = asm.load_full_graph(d)
            with self.assertRaises(ValueError):
                asm.topo_order(nodes)


if __name__ == "__main__":
    unittest.main()

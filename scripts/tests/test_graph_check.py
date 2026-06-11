import json
import os
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import concept_registry as reg  # noqa: E402
import graph_check as gc  # noqa: E402


def write_decomp(graph_dir, slug, atomic, prereqs=(), figurable=None):
    os.makedirs(graph_dir, exist_ok=True)
    data = {
        "concept": {"slug": slug, "name": slug, "definition": f"{slug} def."},
        "audience": "a curious adult with no domain background",
        "atomic": atomic,
        "mechanism_figurable": atomic if figurable is None else figurable,
        "atomic_reason": "test fixture.",
        "prerequisites": [
            {"slug": p, "name": p, "definition": f"{p} def.", "why": "needed."}
            for p in prereqs
        ],
    }
    with open(os.path.join(graph_dir, f"{slug}.json"), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def errors(issues):
    return [m for lvl, m in issues if lvl == "ERROR"]


class TestLoadGraph(unittest.TestCase):
    def test_loads_nodes_and_edges(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "rsa", False, ["mod", "primes"])
            write_decomp(d, "mod", True)
            nodes, issues = gc.load_graph(d)
            self.assertEqual(errors(issues), [])
            self.assertEqual(nodes["rsa"]["prerequisites"], ["mod", "primes"])
            self.assertTrue(nodes["mod"]["atomic"])

    def test_unreadable_file_errors(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "bad.json"), "w") as fh:
                fh.write("{not json")
            nodes, issues = gc.load_graph(d)
            self.assertTrue(errors(issues))

    def test_missing_dir_errors(self):
        nodes, issues = gc.load_graph("/nonexistent/graph")
        self.assertTrue(errors(issues))


class TestCycles(unittest.TestCase):
    def test_acyclic_graph_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", True)
            nodes, _ = gc.load_graph(d)
            self.assertEqual(gc.find_cycles(nodes), [])

    def test_cycle_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b"])
            write_decomp(d, "b", False, ["a"])
            nodes, _ = gc.load_graph(d)
            issues = gc.find_cycles(nodes)
            self.assertTrue(any("cycle" in m for _, m in issues))

    def test_diamond_is_not_a_cycle(self):
        # a -> {b, c}; b -> d; c -> d. The shared prerequisite d is reached
        # twice but is never an ancestor — must NOT be reported as a cycle.
        with tempfile.TemporaryDirectory() as d:
            write_decomp(d, "a", False, ["b", "c"])
            write_decomp(d, "b", False, ["d"])
            write_decomp(d, "c", False, ["d"])
            write_decomp(d, "d", True)
            nodes, _ = gc.load_graph(d)
            self.assertEqual(gc.find_cycles(nodes), [])


class TestCoverage(unittest.TestCase):
    def test_atomic_unregistered_errors(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry)
            self.assertTrue(any("not registered" in m for m in errors(issues)))

    def test_registered_atomic_passes_without_flag(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            nodes, _ = gc.load_graph(graph)
            self.assertEqual(errors(gc.check_coverage(nodes, registry)), [])

    def test_require_illustrated_errors_on_registered_only(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertTrue(any("not illustrated" in m for m in errors(issues)))

    def test_frontier_prereq_warns(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "rsa", False, ["mystery"])
            reg.register(registry, "rsa", "RSA", "rsa def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry)
            warns = [m for lvl, m in issues if lvl == "WARN"]
            self.assertTrue(any("frontier" in m for m in warns))


class TestCliExit(unittest.TestCase):
    def test_clean_graph_exits_0(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "mod", True)
            reg.register(registry, "mod", "Mod", "mod def.")
            self.assertEqual(gc.main([graph, "--registry", registry]), 0)

    def test_cycle_exits_1(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "a", False, ["b"])
            write_decomp(graph, "b", False, ["a"])
            reg.register(registry, "a", "A", "a def.")
            reg.register(registry, "b", "B", "b def.")
            self.assertEqual(gc.main([graph, "--registry", registry]), 1)


class TestFigurableCoverage(unittest.TestCase):
    def test_nonatomic_figurable_unillustrated_errors(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "best-effort", False, ["packets"], figurable=True)
            write_decomp(graph, "packets", True)
            reg.register(registry, "best-effort", "B", "b def.")
            reg.register(registry, "packets", "P", "p def.")
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertTrue(any("not illustrated" in m for m in errors(issues)
                                if "best-effort" in m))

    def test_nonatomic_nonfigurable_is_exempt(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry = os.path.join(base, "g"), os.path.join(base, "r")
            write_decomp(graph, "umbrella", False, ["packets"], figurable=False)
            write_decomp(graph, "packets", True)
            reg.register(registry, "umbrella", "U", "u def.")
            reg.register(registry, "packets", "P", "p def.")
            reg.attach_figure(registry, "packets",
                              _mk_fig(os.path.join(base, "fig")))
            nodes, _ = gc.load_graph(graph)
            issues = gc.check_coverage(nodes, registry, require_illustrated=True)
            self.assertFalse(any("umbrella" in m for m in errors(issues)))


def _mk_fig(d):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": "packets"}, fh)
    return d


if __name__ == "__main__":
    unittest.main()

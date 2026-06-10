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


TINY_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 100">'
            '<text class="t">Tiny figure</text></svg>')


def make_figure(figure_dir, slug, n_frames=2):
    os.makedirs(figure_dir, exist_ok=True)
    frames = []
    for i in range(1, n_frames + 1):
        name = f"frame-{i:02d}.svg"
        with open(os.path.join(figure_dir, name), "w", encoding="utf-8") as fh:
            fh.write(TINY_SVG)
        frames.append({"file": name, "caption": f"Step {i}.",
                       "runbook": f"Frame {i}.", "commentary": f"Step {i}. Simple."})
    with open(os.path.join(figure_dir, "figure.json"), "w", encoding="utf-8") as fh:
        json.dump({"concept_slug": slug, "archetype": "illustrative",
                   "playback": "slideshow" if n_frames > 1 else "static",
                   "frames": frames}, fh)
    return figure_dir


def make_world(base):
    """graph: rsa -> [modular-arithmetic(covered), primes(atomic), asym(atomic)];
    registry: mod covered+illustrated; primes/asym illustrated; rsa registered."""
    graph = os.path.join(base, "out", "graph")
    registry = os.path.join(base, "registry")
    write_decomp(graph, "rsa", False, ["modular-arithmetic", "primes", "asym"])
    write_decomp(graph, "primes", True)
    write_decomp(graph, "asym", True)
    for slug in ("modular-arithmetic", "primes", "asym"):
        reg.register(registry, slug, slug.title(), f"Plain definition of {slug}.")
        reg.attach_figure(registry, slug,
                          make_figure(os.path.join(registry, slug, "figure"), slug))
    reg.register(registry, "rsa", "Rsa", "Plain definition of rsa.")
    return graph, registry, os.path.join(base, "out")


class TestExplainer(unittest.TestCase):
    def test_sections_in_bottom_up_order_root_last(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            result, issues = asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            for s in ("asym", "primes", "rsa"):
                self.assertIn(f'<section id="{s}"', text)
            self.assertLess(text.index('<section id="asym"'), text.index('<section id="rsa"'))
            self.assertLess(text.index('<section id="primes"'), text.index('<section id="rsa"'))

    def test_atomic_nodes_embed_frames_inline(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            # primes + asym: 2 frames each, inline
            self.assertGreaterEqual(text.count("<svg"), 4)

    def test_covered_prereq_is_linked_not_inlined(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            self.assertIn('id="modular-arithmetic"', text)
            self.assertIn("Already covered", text)
            self.assertIn("figure.html", text)  # link target
            # the covered figure's frames are NOT inlined: its viewer link exists
            viewer = os.path.join(registry, "modular-arithmetic", "figure", "figure.html")
            self.assertTrue(os.path.exists(viewer))

    def test_intermediate_root_is_caption_only_with_child_links(self):
        with tempfile.TemporaryDirectory() as base:
            graph, registry, out = make_world(base)
            asm.assemble(graph, registry, out)
            text = open(os.path.join(out, "index.html"), encoding="utf-8").read()
            rsa = text[text.index('<section id="rsa"'):]
            self.assertIn('href="#primes"', rsa)
            self.assertIn("rsa needs primes", rsa)

    def test_frontier_prereq_gets_stub(self):
        with tempfile.TemporaryDirectory() as base:
            graph = os.path.join(base, "out", "graph")
            registry = os.path.join(base, "registry")
            write_decomp(graph, "solo", True, ["mystery-idea"])
            reg.register(registry, "solo", "Solo", "Plain definition of solo.")
            reg.attach_figure(registry, "solo",
                              make_figure(os.path.join(registry, "solo", "figure"), "solo"))
            asm.assemble(graph, registry, os.path.join(base, "out"))
            text = open(os.path.join(base, "out", "index.html"), encoding="utf-8").read()
            self.assertIn("not yet covered", text)
            self.assertIn("mystery-idea", text)


if __name__ == "__main__":
    unittest.main()

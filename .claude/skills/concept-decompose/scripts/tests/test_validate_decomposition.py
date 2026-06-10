import os
import sys
import unittest

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS_DIR)
import validate_decomposition as vd  # noqa: E402


def good():
    return {
        "concept": {"slug": "rsa-encryption", "name": "RSA encryption",
                    "definition": "Two-key secret messaging."},
        "audience": "a curious adult with no domain background",
        "atomic": False,
        "atomic_reason": "Needs clock arithmetic and the two-key idea first.",
        "prerequisites": [
            {"slug": "modular-arithmetic", "name": "Modular arithmetic",
             "definition": "Arithmetic that wraps around, like a clock.",
             "why": "RSA's math is wrap-around math."}
        ],
    }


def errors(data):
    return [m for lvl, m in vd.validate(data) if lvl == "ERROR"]


class TestValidate(unittest.TestCase):
    def test_good_decomposition_is_clean(self):
        self.assertEqual(errors(good()), [])

    def test_missing_concept_fields(self):
        d = good()
        del d["concept"]["definition"]
        self.assertTrue(any("definition" in m for m in errors(d)))

    def test_bad_slug(self):
        d = good()
        d["concept"]["slug"] = "Not A Slug"
        self.assertTrue(any("kebab" in m for m in errors(d)))

    def test_atomic_must_be_bool(self):
        d = good()
        d["atomic"] = "false"
        self.assertTrue(any("atomic" in m for m in errors(d)))

    def test_non_atomic_needs_prerequisites(self):
        d = good()
        d["prerequisites"] = []
        self.assertTrue(any("at least one prerequisite" in m for m in errors(d)))

    def test_atomic_with_empty_prereqs_is_clean(self):
        d = good()
        d["atomic"] = True
        d["atomic_reason"] = "One short clock-face figure explains it."
        d["prerequisites"] = []
        self.assertEqual(errors(d), [])

    def test_prerequisite_missing_why(self):
        d = good()
        del d["prerequisites"][0]["why"]
        self.assertTrue(any("why" in m for m in errors(d)))

    def test_duplicate_prerequisite_slugs(self):
        d = good()
        d["prerequisites"].append(dict(d["prerequisites"][0]))
        self.assertTrue(any("duplicate" in m for m in errors(d)))

    def test_self_prerequisite(self):
        d = good()
        d["prerequisites"][0]["slug"] = "rsa-encryption"
        self.assertTrue(any("own prerequisite" in m for m in errors(d)))


class TestSkillContract(unittest.TestCase):
    SKILL_DIR = os.path.dirname(SCRIPTS_DIR)

    def test_skill_md_references_exist(self):
        import check_skill_refs
        self.assertEqual(check_skill_refs.missing_refs(), [])

    def test_skill_md_covers_the_contract(self):
        with open(os.path.join(self.SKILL_DIR, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        for token in ("decomposition.json", "atomic", "jargon",
                      "one level", "kebab"):
            self.assertIn(token, text, f"SKILL.md missing '{token}'")


class TestGoldenDecompositions(unittest.TestCase):
    EXAMPLES = os.path.join(os.path.dirname(SCRIPTS_DIR), "examples")

    def _load(self, slug):
        import json
        path = os.path.join(self.EXAMPLES, slug, "decomposition.json")
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def test_rsa_is_valid_and_non_atomic(self):
        data = self._load("rsa-encryption")
        self.assertEqual([m for lvl, m in vd.validate(data) if lvl == "ERROR"], [])
        self.assertFalse(data["atomic"])
        self.assertGreaterEqual(len(data["prerequisites"]), 2)

    def test_modular_arithmetic_is_valid_and_atomic(self):
        data = self._load("modular-arithmetic")
        self.assertEqual([m for lvl, m in vd.validate(data) if lvl == "ERROR"], [])
        self.assertTrue(data["atomic"])
        self.assertEqual(data["prerequisites"], [])

    def test_identity_is_consistent_across_examples(self):
        rsa = self._load("rsa-encryption")
        mod = self._load("modular-arithmetic")
        rsa_slugs = {p["slug"] for p in rsa["prerequisites"]}
        self.assertIn(mod["concept"]["slug"], rsa_slugs)


if __name__ == "__main__":
    unittest.main()

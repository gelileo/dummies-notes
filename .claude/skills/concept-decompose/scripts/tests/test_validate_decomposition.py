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


if __name__ == "__main__":
    unittest.main()

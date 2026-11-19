"""Regression and boundary tests for the experiment estimand and published data."""
import hashlib
import sqlite3
import unittest
from dataclasses import replace
from statistics import NormalDist

from promotion.analysis import Arm, compare, contrasts, summarize, wilson
from promotion.data import CONTROL, MENS, WOMENS, RAW, SHA256, load_assignments, read_source, verified_csv


class StatisticsTests(unittest.TestCase):
    def test_wilson_at_edges(self):
        z = NormalDist().inv_cdf(.975)
        a, b = wilson(0, 10, z)
        self.assertAlmostEqual(a, 0)
        self.assertAlmostEqual(b, .277532800, places=8)
        a, b = wilson(10, 10, z)
        self.assertAlmostEqual(a, .722467200, places=8)
        self.assertAlmostEqual(b, 1)
        with self.assertRaises(ValueError):
            wilson(1, 0, z)

    def test_contrast_reverses_with_arms(self):
        a = Arm(MENS, 1000, 500, 90, .09, 0, 0)
        b = replace(a, arm=CONTROL, buyers=60, purchase_rate=.06)
        forward = compare(a, b, 2.4)
        reverse = compare(b, a, 2.4)
        self.assertAlmostEqual(forward.extra_buyers_per_1000, 30)
        self.assertAlmostEqual(forward.ci_low, -reverse.ci_high)
        self.assertAlmostEqual(forward.ci_high, -reverse.ci_low)

    def test_rejects_corrupt_source(self):
        with self.assertRaises(ValueError):
            verified_csv(b"segment,conversion\nMens E-Mail,1\n")

    def test_sql_includes_nonvisitors_and_repeated_rows(self):
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE assignments(segment, visit, conversion, spend_cents)")
            db.executemany("INSERT INTO assignments VALUES (?,?,?,?)",
                           [(CONTROL, 0, 0, 0), (CONTROL, 0, 0, 0), (CONTROL, 1, 1, 1234)])
            arm, = summarize(db)
        self.assertEqual((arm.assigned, arm.visitors, arm.buyers), (3, 1, 1))
        self.assertAlmostEqual(arm.purchase_rate, 1/3)
        self.assertAlmostEqual(arm.spend_per_assigned, 12.34/3)


@unittest.skipUnless(RAW.exists(), "Run python run_analysis.py to cache the real CSV first.")
class PublishedDataTests(unittest.TestCase):
    def test_three_published_arms_and_adjusted_intervals(self):
        payload = read_source(RAW)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), SHA256)
        with sqlite3.connect(":memory:") as db:
            load_assignments(db, payload)
            arms = summarize(db)
        self.assertEqual([(a.arm, a.assigned, a.buyers, a.total_spend_cents) for a in arms], [
            (CONTROL, 21306, 122, 1390833), (MENS, 21307, 267, 3031169),
            (WOMENS, 21387, 189, 2303811)])
        results = contrasts(arms)
        self.assertEqual([(e.treatment, e.comparison) for e in results],
                         [(MENS, CONTROL), (WOMENS, CONTROL), (MENS, WOMENS)])
        for effect, expected in zip(results, [(6.805, 4.619, 9.058), (3.111, 1.143, 5.116),
                                               (3.694, 1.313, 6.106)]):
            for measured, ref in zip((effect.extra_buyers_per_1000, effect.ci_low, effect.ci_high), expected):
                self.assertAlmostEqual(measured, ref, places=3)


if __name__ == "__main__":
    unittest.main()

"""Pairwise differences in purchase probability with simultaneous uncertainty."""
from dataclasses import dataclass
from math import hypot, sqrt
from sqlite3 import Connection, Row
from statistics import NormalDist

from .data import CONTROL, MENS, WOMENS, ROOT

PAIRS = ((MENS, CONTROL), (WOMENS, CONTROL), (MENS, WOMENS))


@dataclass(frozen=True)
class Arm:
    arm: str
    assigned: int
    visitors: int
    buyers: int
    purchase_rate: float
    total_spend_cents: int
    spend_per_assigned: float


@dataclass(frozen=True)
class Contrast:
    treatment: str
    comparison: str
    extra_buyers_per_1000: float
    ci_low: float
    ci_high: float


def summarize(db: Connection) -> list[Arm]:
    db.row_factory = Row
    sql = (ROOT / "sql/arm_summary.sql").read_text(encoding="utf-8")
    return [Arm(**dict(row)) for row in db.execute(sql)]


def wilson(buyers: int, assigned: int, z: float) -> tuple[float, float]:
    if not 0 <= buyers <= assigned or assigned == 0:
        raise ValueError("Expected 0 <= buyers <= assigned and assigned > 0.")
    p = buyers / assigned
    scale = 1 + z * z / assigned
    center = (p + z * z / (2 * assigned)) / scale
    half = z / scale * sqrt(p * (1 - p) / assigned + z * z / (4 * assigned**2))
    return max(0, center - half), min(1, center + half)


def compare(a: Arm, b: Arm, z: float) -> Contrast:
    # Newcombe method 10 for two independent proportions, without continuity correction.
    pa, pb = a.buyers / a.assigned, b.buyers / b.assigned
    la, ua = wilson(a.buyers, a.assigned, z)
    lb, ub = wilson(b.buyers, b.assigned, z)
    diff = pa - pb
    lo = diff - hypot(pa - la, ub - pb)
    hi = diff + hypot(ua - pa, pb - lb)
    return Contrast(a.arm, b.arm, 1000 * diff, 1000 * lo, 1000 * hi)


def contrasts(arms: list[Arm]) -> list[Contrast]:
    by_name = {arm.arm: arm for arm in arms}
    # Two-sided Bonferroni intervals across both versus-control tests and the head-to-head.
    z = NormalDist().inv_cdf(1 - 0.05 / (2 * len(PAIRS)))
    return [compare(by_name[a], by_name[b], z) for a, b in PAIRS]

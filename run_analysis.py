"""Run from any directory with Python 3.10+."""
import argparse
import os
from pathlib import Path
import sqlite3
import tempfile

from promotion.analysis import contrasts, summarize
from promotion.data import RAW, ROOT, load_assignments, read_source
from promotion.report import decision, export


def run(source: Path, reports: Path, database: Path):
    payload = read_source(source)
    database.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=database.parent) as temp:
        staging = Path(temp) / "challenge.sqlite"
        db = sqlite3.connect(staging)
        try:
            load_assignments(db, payload)
            arms = summarize(db)
        finally:
            db.close()
        effects = contrasts(arms)
        export(arms, effects, reports)
        os.replace(staging, database)
    for e in effects:
        print(f"{e.treatment} vs {e.comparison}: {e.extra_buyers_per_1000:+.2f} "
              f"[{e.ci_low:+.2f}, {e.ci_high:+.2f}] buyers per 1,000")
    print(decision(effects))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=RAW, help="CSV cache (fetched if missing)")
    parser.add_argument("--reports", type=Path, default=ROOT / "reports")
    parser.add_argument("--database", type=Path, default=ROOT / "data/hillstrom.sqlite")
    args = parser.parse_args()
    run(args.data, args.reports, args.database)

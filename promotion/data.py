"""Fetch, verify, and import the Hillstrom challenge dataset."""
import csv
import hashlib
import os
import sqlite3
import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "hillstrom.csv"
FILENAME = "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv"
SHA256 = "0e5893329d8b93cefecc571777672028290ab69865718020c78c7284f291aece"
MIRROR_COMMIT = "ea030d860f334485930d4eb5603bdbb02616dc8e"
URLS = (
    f"https://www.minethatdata.com/{FILENAME}",
    f"https://raw.githubusercontent.com/W-Tran/uplift-modelling/{MIRROR_COMMIT}/data/hillstrom/{FILENAME}",
)
COLUMNS = "recency history_segment history mens womens zip_code newbie channel segment visit conversion spend".split()
CONTROL, MENS, WOMENS = "No E-Mail", "Mens E-Mail", "Womens E-Mail"
ASSIGNED = {CONTROL: 21306, MENS: 21307, WOMENS: 21387}


def verified_csv(payload: bytes) -> bytes:
    """Allow Unix or original Windows line endings, but no content changes."""
    canonical = payload.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    if hashlib.sha256(canonical).hexdigest() != SHA256:
        raise ValueError("Hillstrom CSV failed the original SHA-256 check.")
    return canonical


def read_source(path: Path = RAW) -> bytes:
    if path.exists():
        return verified_csv(path.read_bytes())
    path.parent.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in URLS:
        try:
            with urlopen(url, timeout=25) as response:
                data = verified_csv(response.read(5_000_000))
        except (URLError, TimeoutError, ValueError) as exc:
            errors.append(f"{url}: {exc}")
            continue
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
            temp = Path(tmp.name)
            try:
                tmp.write(data)
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        try:
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
        return data
    raise RuntimeError("Download failed. Place the original file in data/raw/hillstrom.csv.\n" + "\n".join(errors))


def load_assignments(db: sqlite3.Connection, payload: bytes) -> None:
    reader = csv.DictReader(StringIO(payload.decode("utf-8"), newline=""))
    if reader.fieldnames != COLUMNS:
        raise ValueError("Unexpected 12-column source schema.")

    def records():
        for row_id, row in enumerate(reader, 1):
            arm = row["segment"]
            visit, buyer = int(row["visit"]), int(row["conversion"])
            cents = Decimal(row["spend"]) * 100
            if (arm not in ASSIGNED or visit not in (0, 1) or buyer not in (0, 1)
                    or buyer > visit or cents < 0 or cents != cents.to_integral_value()
                    or bool(cents) != bool(buyer)):
                raise ValueError(f"Invalid outcome or assignment at source row {row_id}.")
            yield row_id, arm, visit, buyer, int(cents)

    with db:
        db.execute("""CREATE TABLE assignments (
            source_row INTEGER PRIMARY KEY, segment TEXT NOT NULL,
            visit INTEGER NOT NULL, conversion INTEGER NOT NULL, spend_cents INTEGER NOT NULL
        )""")
        db.executemany("INSERT INTO assignments VALUES (?, ?, ?, ?, ?)", records())
        counts = dict(db.execute("SELECT segment, COUNT(*) FROM assignments GROUP BY segment"))
        if counts != ASSIGNED:
            raise ValueError(f"Unexpected group counts: {counts}")

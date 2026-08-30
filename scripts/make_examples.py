"""Example CSVs for trying the upload control by hand.

    uv run python scripts/make_examples.py

One file per path through `mlsandbox.upload.read`, so every refusal can be seen rather
than trusted. The oversized one is generated rather than committed — it is fifty megabytes
of nothing, and a repository is a poor place to keep it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mlsandbox.config import PROJECT_ROOT
from mlsandbox.upload import MAX_BYTES, MAX_FEATURES

EXAMPLES = PROJECT_ROOT / "examples"


def main() -> int:
    EXAMPLES.mkdir(exist_ok=True)
    rng = np.random.default_rng(0)
    written: list[tuple[str, str]] = []

    def write(name: str, frame: pd.DataFrame, expect: str) -> None:
        path = EXAMPLES / name
        frame.to_csv(path, index=False)
        written.append((name, expect))

    # Accepted. Mixed types and a few gaps, so it exercises more than the happy path.
    rows = 400
    price = rng.normal(250_000, 60_000, rows).round(2)
    price[rng.choice(rows, 12, replace=False)] = np.nan
    write(
        "houses.csv",
        pd.DataFrame(
            {
                "size_m2": rng.integers(40, 300, rows),
                "bedrooms": rng.integers(1, 6, rows),
                "city": rng.choice(["Madrid", "Bilbao", "Valencia", "Sevilla"], rows),
                "has_garden": rng.choice([True, False], rows),
                "price": price,
            }
        ),
        "accepted — 400 rows, 5 columns, some gaps",
    )

    # Accepted, with columns excluded rather than the file refused.
    write(
        "houses-with-notes.csv",
        pd.DataFrame(
            {
                "listed_on": pd.date_range("2024-01-01", periods=200).astype(str),
                "agent_note": [f"viewing arranged for flat {i}" for i in range(200)],
                "size_m2": rng.integers(40, 300, 200),
                "price": rng.normal(250_000, 60_000, 200).round(2),
            }
        ),
        "accepted — 2 columns skipped, named on hover",
    )

    write(
        "too-many-columns.csv",
        pd.DataFrame({f"c{i}": rng.normal(size=3) for i in range(MAX_FEATURES + 12)}),
        f"refused — {MAX_FEATURES + 12} columns, limit {MAX_FEATURES}",
    )

    write("header-only.csv", pd.DataFrame(columns=["a", "b", "c"]), "refused — no data rows")
    write("one-column.csv", pd.DataFrame({"only": range(50)}), "refused — nothing to predict from")

    write(
        "all-unsupported.csv",
        pd.DataFrame(
            {
                "note": [f"a distinct remark number {i}" for i in range(50)],
                "reference": [f"REF-{i:05d}" for i in range(50)],
            }
        ),
        "refused — every column is free text",
    )

    (EXAMPLES / "not-a-csv.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    written.append(("not-a-csv.png", "refused — not a CSV"))

    # Big enough to trip the browser's check, which happens before any upload starts.
    # Gitignored: fifty megabytes of noise does not belong in a repository.
    big = EXAMPLES / "too-large.csv"
    chunk = pd.DataFrame(rng.normal(size=(50_000, 12)).round(6))
    with big.open("w") as handle:
        chunk.to_csv(handle, index=False)
        while big.stat().st_size <= MAX_BYTES:
            chunk.to_csv(handle, index=False, header=False)
    written.append(("too-large.csv", f"refused in the browser — {big.stat().st_size / 1e6:.0f} MB"))

    width = max(len(name) for name, _ in written)
    for name, expect in written:
        print(f"  {name:{width}}  {expect}")
    print(f"\nwritten to {EXAMPLES.relative_to(PROJECT_ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

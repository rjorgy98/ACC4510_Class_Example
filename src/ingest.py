from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import ensure_dir, load_data_or_fixture, parse_args


REPORTS_DIR = Path("reports")
CODEBOOK_PATH = REPORTS_DIR / "codebook.csv"


def ingest(use_fixture: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, Path]:
    data, meta, source_path = load_data_or_fixture(use_fixture=use_fixture)
    ensure_dir(REPORTS_DIR)
    meta.codebook.to_csv(CODEBOOK_PATH, index=False)
    return data, meta.codebook, source_path


def main() -> None:
    args = parse_args("Ingest Qualtrics export and build codebook.")
    ingest(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

RAW_FILENAME = "Alternative CPA Pathways Survey_December 31, 2025_09.45.xlsx"
DEFAULT_RAW_PATH = Path("data/raw") / RAW_FILENAME
FALLBACK_RAW_PATH = Path(RAW_FILENAME)
FIXTURE_PATH = Path("tests/fixtures/qualtrics_fixture.csv")


@dataclass
class QualtricsMeta:
    codebook: pd.DataFrame
    question_texts: dict[str, str]
    import_ids: dict[str, str]


def resolve_raw_path(raw_path: Path | None = None) -> Path | None:
    if raw_path:
        return raw_path
    if DEFAULT_RAW_PATH.exists():
        return DEFAULT_RAW_PATH
    if FALLBACK_RAW_PATH.exists():
        return FALLBACK_RAW_PATH
    return None


def load_qualtrics_file(path: Path) -> tuple[pd.DataFrame, QualtricsMeta]:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        raw = pd.read_excel(path, header=None, sheet_name="Alternative CPA Pathways Survey")
    elif path.suffix.lower() == ".csv":
        raw = pd.read_csv(path, header=None)
    else:
        raise ValueError(f"Unsupported file type: {path}")

    if raw.shape[0] < 4:
        raise ValueError("Qualtrics export must have at least 4 rows.")

    column_names = raw.iloc[0].astype(str).tolist()
    question_texts = raw.iloc[1].astype(str).tolist()
    import_ids = raw.iloc[2].astype(str).tolist()

    data = raw.iloc[3:].copy()
    data.columns = column_names

    codebook = pd.DataFrame(
        {
            "column_name": column_names,
            "question_text": question_texts,
            "import_id": import_ids,
        }
    )

    meta = QualtricsMeta(
        codebook=codebook,
        question_texts=dict(zip(column_names, question_texts)),
        import_ids=dict(zip(column_names, import_ids)),
    )

    return data, meta


def standardize_blanks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].replace(r"^\s*$", np.nan, regex=True)
    return df


MOJIBAKE_REPLACEMENTS = {
    "‚Äô": "’",
    "‚Äú": "“",
    "‚Äù": "”",
    "‚Äì": "–",
    "‚Äî": "—",
    "Ã©": "é",
    "Ã¨": "è",
    "Ã¢": "â",
    "Ãª": "ê",
    "Ã¼": "ü",
    "Ã¶": "ö",
}


def fix_mojibake(text: str) -> str:
    fixed = text
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        fixed = fixed.replace(bad, good)
    return fixed


def detect_open_ended_columns(meta: QualtricsMeta) -> list[str]:
    keywords = ["other", "specify", "please", "open", "text", "comment"]
    open_cols = []
    for col, question in meta.question_texts.items():
        if question and isinstance(question, str):
            question_lower = question.lower()
            if any(keyword in question_lower for keyword in keywords):
                open_cols.append(col)
    return open_cols


def find_columns_by_keywords(
    meta: QualtricsMeta,
    keywords_all: Iterable[str] | None = None,
    keywords_any: Iterable[str] | None = None,
) -> list[str]:
    matches = []
    for col, question in meta.question_texts.items():
        if not isinstance(question, str):
            continue
        question_lower = question.lower()
        if keywords_all and not all(keyword in question_lower for keyword in keywords_all):
            continue
        if keywords_any and not any(keyword in question_lower for keyword in keywords_any):
            continue
        matches.append(col)
    return matches


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--use-fixture",
        action="store_true",
        help="Use fixture data instead of the raw Excel file.",
    )
    return parser.parse_args()


def load_data_or_fixture(use_fixture: bool = False) -> tuple[pd.DataFrame, QualtricsMeta, Path]:
    if use_fixture:
        data, meta = load_qualtrics_file(FIXTURE_PATH)
        return data, meta, FIXTURE_PATH

    raw_path = resolve_raw_path()
    if raw_path and raw_path.exists():
        data, meta = load_qualtrics_file(raw_path)
        return data, meta, raw_path

    data, meta = load_qualtrics_file(FIXTURE_PATH)
    return data, meta, FIXTURE_PATH

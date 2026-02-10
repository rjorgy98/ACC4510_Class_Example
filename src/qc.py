from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd

from src.clean import PROCESSED_PATH, clean_data
from src.utils import parse_args

QC_PATH = Path("reports/qc_summary.md")


def qc_summary(df: pd.DataFrame) -> str:
    total_responses = len(df)
    total_columns = len(df.columns)

    finished_dist = df["Finished"].value_counts(dropna=False) if "Finished" in df.columns else pd.Series()
    progress_dist = df["Progress"].describe() if "Progress" in df.columns else pd.Series()

    is_repeat_counts = df["is_repeat"].value_counts(dropna=False) if "is_repeat" in df.columns else pd.Series()
    is_finished_counts = df["is_finished"].value_counts(dropna=False) if "is_finished" in df.columns else pd.Series()

    derived_cols = [
        "undergrad_vs_grad",
        "cpa_intent",
        "aware_alt_pathway_any",
        "impact_on_grad_desire",
    ]
    missingness = df[derived_cols].isna().mean().to_dict() if set(derived_cols).issubset(df.columns) else {}

    date_range = None
    if "StartDate" in df.columns:
        start_min = df["StartDate"].min()
        start_max = df["StartDate"].max()
        if pd.notna(start_min) and pd.notna(start_max):
            date_range = f"{start_min} to {start_max}"

    empty_cols = [col for col in df.columns if df[col].isna().all()]

    lines = [
        "# QC Summary",
        "",
        f"Generated: {datetime.utcnow().isoformat()} UTC",
        "",
        f"- Total responses: {total_responses}",
        f"- Total columns: {total_columns}",
        "",
        "## Finished distribution",
        finished_dist.to_frame("count").to_markdown(),
        "",
        "## Progress distribution",
        progress_dist.to_frame("value").to_markdown(),
        "",
        "## is_repeat counts",
        is_repeat_counts.to_frame("count").to_markdown(),
        "",
        "## is_finished counts",
        is_finished_counts.to_frame("count").to_markdown(),
        "",
        "## Missingness (derived variables)",
        pd.Series(missingness).to_frame("missing_rate").to_markdown() if missingness else "No derived columns.",
        "",
        "## StartDate range",
        date_range or "StartDate not available.",
        "",
        "## Entirely empty columns",
        "\n".join(f"- {col}" for col in empty_cols) if empty_cols else "None.",
        "",
    ]
    return "\n".join(lines)


def run_qc(use_fixture: bool = False) -> None:
    if PROCESSED_PATH.exists():
        df = pd.read_parquet(PROCESSED_PATH)
    else:
        df = clean_data(use_fixture=use_fixture)

    QC_PATH.parent.mkdir(parents=True, exist_ok=True)
    QC_PATH.write_text(qc_summary(df))


def main() -> None:
    args = parse_args("Generate QC summary for cleaned data.")
    run_qc(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis_utils import add_metadata, count_by, simple_bar, write_table_with_metadata
from src.clean import PROCESSED_PATH, clean_data
from src.utils import parse_args


def add_intent_band(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    def band(score: float | int | None) -> str:
        if pd.isna(score):
            return "Unknown"
        if score <= 2:
            return "Low"
        if score == 3:
            return "Medium"
        return "High"
    df["cpa_intent_band"] = df["cpa_intent_score"].apply(band)
    return df


def run_analysis_c(use_fixture: bool = False) -> list[Path]:
    if PROCESSED_PATH.exists():
        df = pd.read_parquet(PROCESSED_PATH)
    else:
        df = clean_data(use_fixture=use_fixture)

    df = add_intent_band(df)
    output_paths: list[Path] = []
    dataset_path = str(PROCESSED_PATH)

    tables = {
        "c_impact_on_grad_overall.csv": (
            "impact_on_grad_desire",
            ["impact_on_grad_desire", "is_finished", "is_repeat"],
        ),
        "c_impact_on_grad_by_undergrad_grad.csv": (
            "impact_on_grad_desire",
            ["undergrad_vs_grad", "impact_on_grad_desire", "is_finished", "is_repeat"],
        ),
        "c_impact_on_grad_by_cpa_intent_band.csv": (
            "impact_on_grad_desire",
            ["cpa_intent_band", "impact_on_grad_desire", "is_finished", "is_repeat"],
        ),
    }

    if "counterfactual_grad_likelihood" in df.columns:
        tables["c_counterfactual_grad_likelihood_overall.csv"] = (
            "counterfactual_grad_likelihood",
            ["counterfactual_grad_likelihood", "is_finished", "is_repeat"],
        )
        tables["c_counterfactual_grad_likelihood_by_segment.csv"] = (
            "counterfactual_grad_likelihood",
            ["undergrad_vs_grad", "counterfactual_grad_likelihood", "is_finished", "is_repeat"],
        )

    for filename, (target_col, group_cols) in tables.items():
        counts, n_used, n_missing = count_by(df, group_cols, target_col)
        metadata = add_metadata(
            dataset_path=dataset_path,
            n_used=n_used,
            n_missing=n_missing,
            notes="Breakdowns include is_finished and is_repeat columns.",
        )
        out_path = Path("reports/tables") / filename
        write_table_with_metadata(counts, out_path, metadata)
        output_paths.append(out_path)

    impact_counts, _, _ = count_by(df, ["impact_on_grad_desire"], "impact_on_grad_desire")
    impact_fig = Path("reports/figures/c_impact_on_grad_overall.png")
    simple_bar(impact_counts, "impact_on_grad_desire", "count", "Impact on Graduate Desire", impact_fig)
    output_paths.append(impact_fig)

    if "counterfactual_grad_likelihood" in df.columns:
        counter_counts, _, _ = count_by(
            df, ["counterfactual_grad_likelihood"], "counterfactual_grad_likelihood"
        )
        counter_fig = Path("reports/figures/c_counterfactual_grad_likelihood_overall.png")
        simple_bar(
            counter_counts,
            "counterfactual_grad_likelihood",
            "count",
            "Counterfactual Graduate Likelihood",
            counter_fig,
        )
        output_paths.append(counter_fig)

    return output_paths


def main() -> None:
    args = parse_args("Run analysis for impact on graduate desire.")
    run_analysis_c(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

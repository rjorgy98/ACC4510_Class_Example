from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis_utils import add_metadata, count_by, simple_bar, write_table_with_metadata
from src.clean import PROCESSED_PATH, clean_data
from src.utils import parse_args


def run_analysis_b(use_fixture: bool = False) -> list[Path]:
    if PROCESSED_PATH.exists():
        df = pd.read_parquet(PROCESSED_PATH)
    else:
        df = clean_data(use_fixture=use_fixture)

    output_paths: list[Path] = []
    dataset_path = str(PROCESSED_PATH)

    tables = {
        "b_cpa_intent_overall.csv": ("cpa_intent", ["cpa_intent", "is_finished", "is_repeat"]),
        "b_cpa_intent_by_undergrad_grad.csv": (
            "cpa_intent",
            ["undergrad_vs_grad", "cpa_intent", "is_finished", "is_repeat"],
        ),
        "b_awareness_overall.csv": (
            "aware_alt_pathway_any",
            ["aware_alt_pathway_any", "is_finished", "is_repeat"],
        ),
        "b_awareness_by_undergrad_grad.csv": (
            "aware_alt_pathway_any",
            ["undergrad_vs_grad", "aware_alt_pathway_any", "is_finished", "is_repeat"],
        ),
        "b_awareness_x_cpa_intent.csv": (
            "cpa_intent",
            ["aware_alt_pathway_any", "cpa_intent", "is_finished", "is_repeat"],
        ),
    }

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

    intent_counts, _, _ = count_by(df, ["cpa_intent"], "cpa_intent")
    intent_fig = Path("reports/figures/b_cpa_intent_overall.png")
    simple_bar(intent_counts, "cpa_intent", "count", "CPA Intent (Overall)", intent_fig)
    output_paths.append(intent_fig)

    awareness_counts, _, _ = count_by(df, ["aware_alt_pathway_any"], "aware_alt_pathway_any")
    awareness_fig = Path("reports/figures/b_awareness_overall.png")
    simple_bar(awareness_counts, "aware_alt_pathway_any", "count", "Awareness of Alternative Pathway", awareness_fig)
    output_paths.append(awareness_fig)

    return output_paths


def main() -> None:
    args = parse_args("Run analysis for CPA intent and awareness.")
    run_analysis_b(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

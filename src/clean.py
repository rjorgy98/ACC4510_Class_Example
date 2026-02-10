from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.ingest import ingest
from src.utils import (
    QualtricsMeta,
    detect_open_ended_columns,
    find_columns_by_keywords,
    fix_mojibake,
    parse_args,
    standardize_blanks,
)

PROCESSED_PATH = Path("data/processed/survey_clean.parquet")


def _map_undergrad_grad(value: str | float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Unknown"
    text = str(value).lower()
    if any(term in text for term in ["undergraduate", "undergrad", "bachelor"]):
        return "Undergraduate"
    if any(term in text for term in ["graduate", "master", "mba", "ms", "ma"]):
        return "Graduate"
    return "Unknown"


def _map_yes_no(value: str | float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Unknown"
    text = str(value).strip().lower()
    if text in {"yes", "y", "1", "true"}:
        return "Yes"
    if text in {"no", "n", "0", "false"}:
        return "No"
    return "Unknown"


CPA_INTENT_LABELS = [
    "Very unlikely",
    "Unlikely",
    "Neutral",
    "Likely",
    "Very likely",
]


def _map_likert_5(value: str | float | int | None) -> tuple[str, float | None]:
    if value is None or pd.isna(value):
        return "Unknown", None
    text = str(value).strip().lower()
    mapping = {
        "very unlikely": ("Very unlikely", 1),
        "not at all likely": ("Very unlikely", 1),
        "unlikely": ("Unlikely", 2),
        "neutral": ("Neutral", 3),
        "neither likely nor unlikely": ("Neutral", 3),
        "likely": ("Likely", 4),
        "very likely": ("Very likely", 5),
    }
    for key, mapped in mapping.items():
        if key in text:
            return mapped
    return "Unknown", None


def _map_impact(value: str | float | int | None) -> str:
    if value is None or pd.isna(value):
        return "Unknown"
    text = str(value).strip().lower()
    if "decrease" in text:
        return "Decreased"
    if "increase" in text:
        return "Increased"
    if "no change" in text or "no effect" in text:
        return "No change"
    return "Unknown"


def derive_columns(df: pd.DataFrame, meta: QualtricsMeta) -> pd.DataFrame:
    df = df.copy()

    undergrad_cols = find_columns_by_keywords(meta, keywords_any=["undergraduate", "graduate", "program"])
    cpa_intent_cols = find_columns_by_keywords(
        meta, keywords_all=["likelihood"], keywords_any=["cpa", "license"]
    )
    awareness_cols = find_columns_by_keywords(meta, keywords_any=["aware", "awareness", "alternative pathway"])
    impact_cpa_cols = find_columns_by_keywords(meta, keywords_any=["impact"], keywords_all=["cpa"])
    impact_grad_cols = find_columns_by_keywords(meta, keywords_any=["impact"], keywords_all=["graduate"])
    counterfactual_cols = find_columns_by_keywords(
        meta, keywords_any=["how likely"], keywords_all=["graduate"]
    )
    repeat_cols = find_columns_by_keywords(meta, keywords_any=["already", "taken"], keywords_all=["survey"])

    if undergrad_cols:
        df["undergrad_vs_grad"] = df[undergrad_cols[0]].apply(_map_undergrad_grad)
    else:
        df["undergrad_vs_grad"] = "Unknown"

    cpa_scores = []
    cpa_labels = []
    if cpa_intent_cols:
        for value in df[cpa_intent_cols[0]]:
            label, score = _map_likert_5(value)
            cpa_labels.append(label)
            cpa_scores.append(score)
    else:
        cpa_labels = ["Unknown"] * len(df)
        cpa_scores = [None] * len(df)

    df["cpa_intent"] = pd.Categorical(cpa_labels, categories=CPA_INTENT_LABELS + ["Unknown"], ordered=True)
    df["cpa_intent_score"] = pd.to_numeric(pd.Series(cpa_scores), errors="coerce")

    aware_any_values = []
    if awareness_cols:
        for col in awareness_cols:
            mapped = df[col].apply(_map_yes_no)
            df[f"{col}_aware_mapped"] = mapped
        for idx in df.index:
            row_vals = [df.loc[idx, f"{col}_aware_mapped"] for col in awareness_cols]
            aware_any_values.append("Yes" if "Yes" in row_vals else "No" if "No" in row_vals else "Unknown")
    else:
        aware_any_values = ["Unknown"] * len(df)

    df["aware_alt_pathway"] = (
        df[awareness_cols[0]].apply(_map_yes_no) if awareness_cols else "Unknown"
    )
    df["aware_alt_pathway_any"] = aware_any_values

    if impact_cpa_cols:
        df["impact_on_cpa_desire"] = df[impact_cpa_cols[0]].apply(_map_impact)
    else:
        df["impact_on_cpa_desire"] = "Unknown"

    if impact_grad_cols:
        df["impact_on_grad_desire"] = df[impact_grad_cols[0]].apply(_map_impact)
    else:
        df["impact_on_grad_desire"] = "Unknown"

    if counterfactual_cols:
        counter_labels = []
        for value in df[counterfactual_cols[0]]:
            label, _ = _map_likert_5(value)
            counter_labels.append(label)
        df["counterfactual_grad_likelihood"] = pd.Categorical(
            counter_labels, categories=CPA_INTENT_LABELS + ["Unknown"], ordered=True
        )
    else:
        df["counterfactual_grad_likelihood"] = "Unknown"

    if repeat_cols:
        df["is_repeat"] = df[repeat_cols[0]].apply(_map_yes_no).replace({"Yes": True, "No": False, "Unknown": np.nan})
    else:
        df["is_repeat"] = np.nan

    if "Finished" in df.columns:
        df["is_finished"] = df["Finished"].apply(lambda x: True if str(x).strip() in {"1", "True", "true"} else False)
    else:
        df["is_finished"] = np.nan

    df["response_weight"] = 1

    return df


def clean_data(use_fixture: bool = False) -> pd.DataFrame:
    data, codebook, _source_path = ingest(use_fixture=use_fixture)
    meta = QualtricsMeta(
        codebook=codebook,
        question_texts=dict(zip(codebook["column_name"], codebook["question_text"])),
        import_ids=dict(zip(codebook["column_name"], codebook["import_id"])),
    )

    data = standardize_blanks(data)

    for date_col in ["StartDate", "EndDate", "RecordedDate"]:
        if date_col in data.columns:
            data[date_col] = pd.to_datetime(data[date_col], errors="coerce")

    if "Finished" in data.columns:
        data["Finished"] = data["Finished"].astype(str).str.strip().replace({"": np.nan})

    for numeric_col in ["Progress", "Duration (in seconds)"]:
        if numeric_col in data.columns:
            data[numeric_col] = pd.to_numeric(data[numeric_col], errors="coerce")

    open_cols = detect_open_ended_columns(meta)
    for col in open_cols:
        if col in data.columns:
            data[f"{col}_clean"] = data[col].astype(str).apply(fix_mojibake)

    data = derive_columns(data, meta)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(PROCESSED_PATH, index=False)

    return data


def main() -> None:
    args = parse_args("Clean Qualtrics export and create derived columns.")
    clean_data(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

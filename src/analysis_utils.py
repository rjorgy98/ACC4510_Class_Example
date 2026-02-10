from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


TABLES_DIR = Path("reports/tables")
FIGURES_DIR = Path("reports/figures")


def write_table_with_metadata(df: pd.DataFrame, path: Path, metadata: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for key, value in metadata.items():
            handle.write(f"# {key}: {value}\n")
        df.to_csv(handle, index=False)


def add_metadata(dataset_path: str, n_used: int, n_missing: int, notes: str) -> dict[str, str]:
    return {
        "dataset_path": dataset_path,
        "run_timestamp": datetime.utcnow().isoformat() + "Z",
        "n_used": str(n_used),
        "n_missing": str(n_missing),
        "notes": notes,
    }


def simple_bar(df: pd.DataFrame, category_col: str, count_col: str, title: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.bar(df[category_col].astype(str), df[count_col])
    plt.title(title)
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def count_by(df: pd.DataFrame, group_cols: list[str], target_col: str | None = None) -> tuple[pd.DataFrame, int, int]:
    if target_col:
        missing = df[target_col].isna().sum()
        data = df.dropna(subset=[target_col])
    else:
        missing = 0
        data = df
    n_used = len(data)
    counts = data.groupby(group_cols, dropna=False).size().reset_index(name="count")
    counts["pct_total"] = counts["count"] / n_used if n_used else 0
    return counts, n_used, int(missing)

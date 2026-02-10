from __future__ import annotations

from datetime import datetime
from pathlib import Path
import platform
import subprocess
from io import StringIO

import pandas as pd

from src.analysis_b import run_analysis_b
from src.analysis_c import run_analysis_c
from src.clean import PROCESSED_PATH, clean_data
from src.qc import run_qc
from src.utils import parse_args

MEMO_PATH = Path("reports/memo.md")


def _get_git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def read_table_with_metadata(path: Path) -> tuple[dict[str, str], pd.DataFrame]:
    metadata: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    data_lines = []
    for line in lines:
        if line.startswith("# "):
            key_value = line[2:].strip().split(":", 1)
            if len(key_value) == 2:
                metadata[key_value[0].strip()] = key_value[1].strip()
        else:
            data_lines.append(line)
    df = pd.read_csv(StringIO("".join(data_lines)))
    return metadata, df


def build_memo(tables: list[Path], figures: list[Path]) -> str:
    run_time = datetime.utcnow().isoformat() + "Z"
    git_hash = _get_git_hash()
    python_version = platform.python_version()

    lines = [
        "# Alternative CPA Pathways Survey Memo",
        "",
        "## Run metadata",
        f"- Timestamp (UTC): {run_time}",
        f"- Git commit: {git_hash}",
        f"- Python version: {python_version}",
        "",
        "## Core outputs",
        "- [Codebook](codebook.csv)",
        "- [QC summary](qc_summary.md)",
        "",
        "## Tables",
    ]

    for table in sorted(tables):
        metadata, _df = read_table_with_metadata(table)
        n_used = metadata.get("n_used", "unknown")
        n_missing = metadata.get("n_missing", "unknown")
        lines.append(f"- [{table.name}](tables/{table.name}) (N used: {n_used}, N missing: {n_missing})")

    lines.append("")
    lines.append("## Figures")
    for figure in sorted(figures):
        lines.append(f"- ![{figure.name}](figures/{figure.name})")

    lines.append("")
    lines.append("## Key distributions")

    key_tables = [
        "b_cpa_intent_overall.csv",
        "b_awareness_overall.csv",
        "c_impact_on_grad_overall.csv",
    ]
    for name in key_tables:
        path = Path("reports/tables") / name
        if path.exists():
            _metadata, df = read_table_with_metadata(path)
            lines.append("")
            lines.append(f"### {name}")
            lines.append(df.head(10).to_markdown(index=False))

    lines.extend(
        [
            "",
            "## Next analysis questions (B & C)",
            "1. How does CPA intent vary between undergraduate and graduate respondents when excluding repeats?",
            "2. Are awareness levels higher among finished respondents compared with unfinished ones?",
            "3. Does awareness correlate with higher CPA intent bands across segments?",
            "4. What share of respondents report increased graduate desire after learning about the alternative pathway?",
            "5. How does impact on graduate desire differ by CPA intent band?",
            "6. Are repeat respondents systematically different in awareness or intent distributions?",
            "7. How does counterfactual graduate likelihood compare between undergrad and grad groups?",
            "8. What is the distribution of CPA intent among those reporting decreased graduate desire?",
            "9. Are there notable differences in awareness by program level when limiting to finished responses?",
            "10. How sensitive are results to treating unknown awareness responses as missing?",
        ]
    )

    lines.append("")
    return "\n".join(lines)


def run_memo(use_fixture: bool = False) -> None:
    if not PROCESSED_PATH.exists():
        clean_data(use_fixture=use_fixture)

    run_qc(use_fixture=use_fixture)
    tables_b = run_analysis_b(use_fixture=use_fixture)
    tables_c = run_analysis_c(use_fixture=use_fixture)

    tables = [path for path in tables_b + tables_c if path.suffix == ".csv"]
    figures = [path for path in tables_b + tables_c if path.suffix == ".png"]

    memo_content = build_memo(tables, figures)
    MEMO_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEMO_PATH.write_text(memo_content)


def main() -> None:
    args = parse_args("Generate consolidated memo for analyses.")
    run_memo(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

from __future__ import annotations

from src.analysis_b import run_analysis_b
from src.analysis_c import run_analysis_c
from src.clean import clean_data
from src.ingest import ingest
from src.memo import run_memo
from src.qc import run_qc
from src.utils import parse_args


def run_pipeline(use_fixture: bool = False) -> None:
    ingest(use_fixture=use_fixture)
    clean_data(use_fixture=use_fixture)
    run_qc(use_fixture=use_fixture)
    run_analysis_b(use_fixture=use_fixture)
    run_analysis_c(use_fixture=use_fixture)
    run_memo(use_fixture=use_fixture)


def main() -> None:
    args = parse_args("Run the full analysis pipeline.")
    run_pipeline(use_fixture=args.use_fixture)


if __name__ == "__main__":
    main()

# ACC4510_Class_Example

## Overview
This repository provides a fully reproducible Python workflow to ingest, clean, quality-check, and analyze a Qualtrics-style Excel export focused on CPA intention, awareness of the alternative pathway, and how awareness changes graduate degree intent.

## Quick start
```bash
make install
make run
```

## Workflow
The pipeline runs end-to-end with a single command:
```bash
python -m src.pipeline
```
This performs:
1. Ingest (`src/ingest.py`) and codebook generation.
2. Cleaning and derived variables (`src/clean.py`).
3. QC summary (`src/qc.py`).
4. Analysis for sections B and C (`src/analysis_b.py`, `src/analysis_c.py`).
5. Memo generation (`src/memo.py`).

To only generate QC:
```bash
make qc
```

To clean outputs:
```bash
make clean-outputs
```

## Outputs
Outputs are written to:
- `data/processed/survey_clean.parquet`
- `reports/codebook.csv`
- `reports/qc_summary.md`
- `reports/tables/` (CSV tables)
- `reports/figures/` (PNG figures)
- `reports/memo.md`

## Reproducibility
The pipeline is deterministic given the same input Excel export and code. Re-run with `make run` to regenerate all outputs from scratch.

## CI behavior
GitHub Actions runs tests and the pipeline with a small fixture dataset located in `tests/fixtures/`. The pipeline automatically falls back to the fixture if the real Excel file is not present. This ensures CI remains reproducible without requiring access to raw data.

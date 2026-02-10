from pathlib import Path

import pandas as pd

from src.clean import clean_data
from src.ingest import ingest
from src.pipeline import run_pipeline
from src.utils import FIXTURE_PATH


def test_ingest_fixture():
    data, codebook, source = ingest(use_fixture=True)
    assert source == FIXTURE_PATH
    assert not data.empty
    assert {"column_name", "question_text", "import_id"}.issubset(codebook.columns)


def test_clean_derivations():
    df = clean_data(use_fixture=True)
    required = {
        "undergrad_vs_grad",
        "cpa_intent",
        "cpa_intent_score",
        "aware_alt_pathway",
        "aware_alt_pathway_any",
        "impact_on_cpa_desire",
        "impact_on_grad_desire",
        "counterfactual_grad_likelihood",
        "is_repeat",
        "is_finished",
        "response_weight",
    }
    assert required.issubset(df.columns)
    assert df["cpa_intent_score"].notna().any()


def test_pipeline_outputs(tmp_path):
    run_pipeline(use_fixture=True)
    assert Path("data/processed/survey_clean.parquet").exists()
    assert Path("reports/memo.md").exists()
    assert any(Path("reports/tables").glob("*.csv"))
    assert any(Path("reports/figures").glob("*.png"))
    parquet = pd.read_parquet("data/processed/survey_clean.parquet")
    assert not parquet.empty

.PHONY: install run qc clean-outputs

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	python -m src.pipeline

qc:
	python -m src.qc

clean-outputs:
	rm -rf reports/tables/* reports/figures/* reports/memo.md reports/codebook.csv reports/qc_summary.md data/processed/*

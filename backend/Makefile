# ==============================================================================
# FinPulse AI — Backend ML Pipeline & Development Automation
# ==============================================================================

.PHONY: help collect collect-synthetic features targets train backtest pipeline pipeline-synthetic test lint

help:
	@echo "Available targets:"
	@echo "  make pipeline            Run full pipeline using available real/sample data"
	@echo "  make pipeline-synthetic  Run full pipeline with fresh synthetic sample data"
	@echo "  make collect             Collect market data from Upstox (requires token)"
	@echo "  make collect-synthetic   Generate labeled synthetic sample market data"
	@echo "  make features            Generate point-in-time technical features"
	@echo "  make targets             Generate forward 5-day return targets"
	@echo "  make train               Train XGBoost classifier & baselines"
	@echo "  make backtest            Run out-of-sample vectorized backtest"
	@echo "  make test                Run pytest test suite"

collect:
	python -m app.ml.pipeline.collect_data

collect-synthetic:
	python -m app.ml.pipeline.collect_data --synthetic

features:
	python -m app.ml.pipeline.build_features

targets:
	python -m app.ml.pipeline.build_targets

train:
	python -m app.ml.pipeline.train_xgboost

backtest:
	python -m app.ml.pipeline.backtest

pipeline: features targets train backtest
	@echo "Pipeline execution completed successfully."

pipeline-synthetic: collect-synthetic features targets train backtest
	@echo "Synthetic pipeline execution completed successfully."

test:
	pytest tests/

test-pipeline:
	pytest tests/test_ml/

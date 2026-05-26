.PHONY: install dev run test clean init-db

PYTHON = .venv/bin/python3
STREAMLIT = .venv/bin/streamlit

install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

dev:
	$(STREAMLIT) run app_phase1/main.py

init-db:
	$(PYTHON) scripts/init_db.py

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	.venv/bin/ruff check core/ app_phase1/

clean:
	rm -rf data/ .venv/ *.egg-info/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

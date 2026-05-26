FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pip setuptools --upgrade

COPY pyproject.toml .
COPY core/ ./core/
COPY api/ ./api/
COPY scripts/ ./scripts/

RUN pip install --no-cache-dir -e .

ENV DATABASE_URL=sqlite:///app/data/stock.db

EXPOSE 8000

CMD mkdir -p /app/data && uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}

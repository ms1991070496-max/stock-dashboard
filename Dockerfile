FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY core/ ./core/
COPY api/ ./api/
COPY scripts/ ./scripts/

RUN pip install --no-cache-dir -e .

ENV DATABASE_URL=sqlite:///data/stock.db

RUN mkdir -p /app/data && python -c "from core.database import init_db; init_db()"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

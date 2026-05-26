FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pip setuptools --upgrade

COPY pyproject.toml .
COPY core/ ./core/
COPY api/ ./api/

RUN pip install --no-cache-dir -e .

ENV DATABASE_URL=sqlite:///:memory:

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

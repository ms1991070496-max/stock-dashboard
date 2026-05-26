FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir pip setuptools --upgrade \
    && pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings \
       sqlalchemy pandas numpy httpx diskcache yfinance vader-sentiment

COPY core/ ./core/
COPY api/ ./api/

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///:memory:

RUN python -c "from api.main import app; print('Routes:', [r.path for r in app.routes])"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

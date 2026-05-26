FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY core/ ./core/
COPY api/ ./api/
COPY static/ ./static/

ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///:memory:

EXPOSE 8000

CMD uvicorn api.main:app --host 0.0.0.0 --port 8000

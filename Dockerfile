FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn

COPY api/ ./api/
COPY core/ ./core/

ENV PYTHONPATH=/app

# Test: simple app first
RUN python -c "
from fastapi import FastAPI
app = FastAPI()
@app.get('/api/health')
def h(): return {'ok': True}
print('OK routes:', [r.path for r in app.routes])
"

# Test: our app
RUN pip install --no-cache-dir pydantic pydantic-settings sqlalchemy pandas numpy httpx \
    && python -c "from api.main import app; print('OUR routes:', [r.path for r in app.routes])"

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}

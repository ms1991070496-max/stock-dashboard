FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pip setuptools --upgrade

COPY pyproject.toml .
COPY core/ ./core/
COPY api/ ./api/
COPY scripts/ ./scripts/
COPY start.sh .

RUN pip install --no-cache-dir -e . && chmod +x start.sh

ENV DATABASE_URL=sqlite:///app/data/stock.db

EXPOSE 8000

CMD ["./start.sh"]

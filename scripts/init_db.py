"""Initialize database and optionally seed demo stocks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import init_db, SessionLocal
from core.models import Stock
from core.fetchers.demo_data import DEMO_STOCKS


def main():
    init_db()
    print("Database initialized successfully.")

    db = SessionLocal()
    try:
        for code, info in DEMO_STOCKS.items():
            if not db.query(Stock).filter(Stock.code == code).first():
                db.add(Stock(code=code, name=info["name"], market=info["market"]))
        db.commit()
        count = db.query(Stock).count()
        print(f"Seeded {count} demo stocks.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

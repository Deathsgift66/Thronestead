from backend.database import SessionLocal
from services.spies_service import reset_daily_attack_counts


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")
    with SessionLocal() as db:
        rows = reset_daily_attack_counts(db)
        print(f"Reset daily spy attack counters for {rows} kingdoms")


if __name__ == "__main__":
    main()

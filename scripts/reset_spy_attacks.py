from backend.database import session_local
from services.spies_service import reset_daily_attack_counts


def main() -> None:
    if session_local is None:
        raise RuntimeError("DATABASE_URL not configured")
    with session_local() as db:
        rows = reset_daily_attack_counts(db)
        print(f"Reset daily spy attack counters for {rows} kingdoms")


if __name__ == "__main__":
    main()

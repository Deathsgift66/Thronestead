from .db_utils import get_session
from services.spies_service import reset_daily_attack_counts


def main() -> None:
    with get_session() as db:
        rows = reset_daily_attack_counts(db)
        print(f"Reset daily spy attack counters for {rows} kingdoms")


if __name__ == "__main__":
    main()

from backend.database import SessionLocal
from services.realtime_fallback_service import (
    finalize_overdue_training,
    fallback_on_idle_training,
    mark_stale_engaged_units_defeated,
)


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")

    with SessionLocal() as db:
        completed = finalize_overdue_training(db)
        completed += fallback_on_idle_training(db)
        defeated = mark_stale_engaged_units_defeated(db)
        print(f"Completed {completed} training orders")
        print(f"Marked {defeated} units defeated")


if __name__ == "__main__":
    main()

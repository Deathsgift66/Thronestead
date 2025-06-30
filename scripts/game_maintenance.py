from backend.database import SessionLocal
from services.maintenance_service import (
    verify_kingdom_resources,
    cleanup_zombie_training_queue,
    cleanup_zombie_spy_missions,
)


def main() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")
    with SessionLocal() as db:
        count = verify_kingdom_resources(db)
        print(f"Verified resources for {count} kingdoms")

        removed = cleanup_zombie_training_queue(db)
        print(f"Removed {removed} stale training orders")

        expired = cleanup_zombie_spy_missions(db)
        print(f"Expired {expired} spy missions")


if __name__ == "__main__":
    main()

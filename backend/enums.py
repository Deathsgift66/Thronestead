from enum import Enum

class WarPhase(str, Enum):
    """Phases for tactical wars."""

    ALERT = "alert"
    PLANNING = "planning"
    LIVE = "live"
    RESOLVED = "resolved"


class QuestStatusKingdom(str, Enum):
    """Status values for kingdom quests."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


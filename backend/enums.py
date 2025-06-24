from enum import Enum

class WarPhase(str, Enum):
    """Phases for tactical wars."""

    ALERT = "alert"
    PLANNING = "planning"
    LIVE = "live"
    RESOLVED = "resolved"


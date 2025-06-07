CASTLE_XP_THRESHOLD = 100

castle_state = {
    "level": 1,
    "xp": 0,
}

nobles = []

# knights stored as id -> {"rank": int}
knights = {}

def progress_castle(xp_gain: int) -> int:
    """Increase castle XP and level up when threshold reached.

    Returns the new castle level.
    """
    castle_state["xp"] += xp_gain
    if castle_state["xp"] >= CASTLE_XP_THRESHOLD:
        castle_state["level"] += 1
        castle_state["xp"] = 0
    return castle_state["level"]

def add_noble(name: str) -> None:
    """Add a noble to the nobles list if not already present."""
    if name not in nobles:
        nobles.append(name)

def remove_noble(name: str) -> None:
    """Remove a noble if present."""
    if name in nobles:
        nobles.remove(name)

def add_knight(knight_id: str, rank: int = 1) -> None:
    """Register a new knight with the given rank."""
    knights[knight_id] = {"rank": rank}

def promote_knight(knight_id: str) -> int:
    """Increase a knight's rank and return the new rank."""
    if knight_id not in knights:
        raise ValueError("Knight not found")
    knights[knight_id]["rank"] += 1
    return knights[knight_id]["rank"]

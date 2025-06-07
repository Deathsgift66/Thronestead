# Simple in-memory data store for the demo API

# Recruitable units for all kingdoms
recruitable_units = [
    {
        "id": 1,
        "name": "Swordsman",
        "type": "Infantry",
        "training_time": 60,
        "cost": {"gold": 10, "food": 5},
    },
    {
        "id": 2,
        "name": "Archer",
        "type": "Ranged",
        "training_time": 45,
        "cost": {"gold": 8, "wood": 5},
    },
]

# Kingdom military state keyed by kingdom_id
military_state = {
    1: {
        "base_slots": 20,
        "used_slots": 0,
        "morale": 100,
        "queue": [],
        "history": [],
    }
}

# Simplified castle progression tracking
castle_progression_state = {
    1: {
        "castle_level": 1,
        "nobles": 0,
        "knights": 0,
    }
}

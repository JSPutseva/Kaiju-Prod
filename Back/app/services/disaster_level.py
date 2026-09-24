from enum import IntEnum


class DisasterLevel(IntEnum):
    WATCH = 1
    ALERT = 2
    EMERGENCY = 3
    CRITICAL = 4
    CATASTROPHIC = 5


DISASTER_LEVELS = {
    DisasterLevel.WATCH: {
        "code": "L1",
        "name": "Watch",
        "description": "Monitoring only. Resources remain in place.",
    },
    DisasterLevel.ALERT: {
        "code": "L2",
        "name": "Alert",
        "description": "Reservations are allowed within the quarter only.",
    },
    DisasterLevel.EMERGENCY: {
        "code": "L3",
        "name": "Emergency",
        "description": "Adjacent transfers are authorized with QC approval.",
    },
    DisasterLevel.CRITICAL: {
        "code": "L4",
        "name": "Critical",
        "description": (
            "Extended transfers are authorized. "
            "Transit chains can be organized by the LC."
        ),
    },
    DisasterLevel.CATASTROPHIC: {
        "code": "L5",
        "name": "Catastrophic",
        "description": (
            "All transfers are unlocked. Maritime routes are prioritized "
            "and the retention threshold may be reduced to 15% by the CD."
        ),
    },
}


def is_valid_disaster_level(level: int) -> bool:
    return level in {item.value for item in DisasterLevel}


def get_disaster_level_definition(level: int) -> dict:
    if not is_valid_disaster_level(level):
        raise ValueError(f"Invalid disaster level: {level}")

    return DISASTER_LEVELS[DisasterLevel(level)]
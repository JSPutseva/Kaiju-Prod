import pytest

from app.services.disaster_level import (
    DISASTER_LEVELS,
    DisasterLevel,
    get_disaster_level_definition,
    is_valid_disaster_level,
)


def test_all_disaster_levels_are_defined():
    assert len(DISASTER_LEVELS) == 5

    assert DisasterLevel.WATCH in DISASTER_LEVELS
    assert DisasterLevel.ALERT in DISASTER_LEVELS
    assert DisasterLevel.EMERGENCY in DISASTER_LEVELS
    assert DisasterLevel.CRITICAL in DISASTER_LEVELS
    assert DisasterLevel.CATASTROPHIC in DISASTER_LEVELS


@pytest.mark.parametrize(
    ("level", "code", "name"),
    [
        (1, "L1", "Watch"),
        (2, "L2", "Alert"),
        (3, "L3", "Emergency"),
        (4, "L4", "Critical"),
        (5, "L5", "Catastrophic"),
    ],
)
def test_disaster_level_definition(level, code, name):
    definition = get_disaster_level_definition(level)

    assert definition["code"] == code
    assert definition["name"] == name
    assert definition["description"]


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_valid_disaster_levels(level):
    assert is_valid_disaster_level(level) is True


@pytest.mark.parametrize("level", [0, -1, 6, 7, 100])
def test_invalid_disaster_levels(level):
    assert is_valid_disaster_level(level) is False


@pytest.mark.parametrize("level", [0, -1, 6, 7, 100])
def test_invalid_disaster_level_definition_raises(level):
    with pytest.raises(
        ValueError,
        match=f"Invalid disaster level: {level}",
    ):
        get_disaster_level_definition(level)
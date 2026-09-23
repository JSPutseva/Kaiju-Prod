import pytest

from app.models.role import UserRole
from app.services.transfer_validation import (
    TransferValidationResult,
    TransferValidator,
    ValidationReason,
)


@pytest.fixture
def validator():
    return TransferValidator()


def test_l1_transfer_rejected(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=1,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.DISASTER_LEVEL_TOO_LOW


def test_l2_transfer_rejected(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=2,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.DISASTER_LEVEL_TOO_LOW


def test_l3_adjacent_transfer_requires_qc_approval(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.QC_APPROVAL_REQUIRED


def test_l3_adjacent_transfer_allowed_with_qc_approval(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        qc_approved=True,
    )

    assert result.allowed
    assert result.reason == ValidationReason.ALLOWED


def test_l3_non_adjacent_transfer_rejected(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        qc_approved=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.NON_ADJACENT_TRANSFER


def test_insufficient_resource_rejected(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=3,
        quantity=10,
        initial_quantity=12,
        available_quantity=5,
        qc_approved=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.INSUFFICIENT_AVAILABLE_RESOURCE


def test_retention_limit_rejected(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=3,
        quantity=9,
        initial_quantity=12,
        available_quantity=12,
        qc_approved=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.RETENTION_LIMIT


def test_l4_non_adjacent_transfer_allowed(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed
    assert result.reason == ValidationReason.ALLOWED


def test_l5_uses_15_percent_retention(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=10,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed
    assert result.reason == ValidationReason.ALLOWED


def test_sea_is_not_a_quarter(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="SEA",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        qc_approved=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.INVALID_QUARTER


def test_maritime_requires_sea_access(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=5,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        maritime=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.MARITIME_NOT_ALLOWED


def test_l4_non_adjacent_transfer_auto_picks_transit(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed
    assert result.route_type == "transit"
    assert result.transit_via == "Warden"
    assert not result.deprioritized_behind_xeno


def test_l4_transit_through_xeno_is_deprioritized(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Echo",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed
    assert result.transit_via == "Xeno"
    assert result.deprioritized_behind_xeno


def test_l4_explicit_valid_transit_is_accepted(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        transit_via="Xeno",
    )

    assert result.allowed
    assert result.route_type == "transit"
    assert result.transit_via == "Xeno"


def test_l4_explicit_invalid_transit_is_rejected(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        transit_via="Echo",
    )

    assert not result.allowed
    assert result.reason == ValidationReason.INVALID_TRANSIT_QUARTER


def test_l4_adjacent_surplus_takes_priority(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        adjacent_surplus={"Warden": 5},
    )

    assert not result.allowed
    assert result.reason == ValidationReason.ADJACENT_SURPLUS_AVAILABLE


def test_direct_adjacent_transfer_has_no_transit(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        qc_approved=True,
    )

    assert result.allowed
    assert result.route_type == "direct"
    assert result.transit_via is None
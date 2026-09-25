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


def test_l5_still_defaults_to_30_percent_retention_without_override(validator):
    # only a CD-invoked override drops the floor to 15% — it's not automatic
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=10,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.RETENTION_LIMIT


def test_l5_cd_can_invoke_15_percent_retention_override(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=10,
        initial_quantity=12,
        available_quantity=12,
        retention_override=True,
    )

    assert result.allowed
    assert result.reason == ValidationReason.ALLOWED


def test_retention_override_rejected_for_non_cd(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=10,
        initial_quantity=12,
        available_quantity=12,
        retention_override=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.PERMISSION_DENIED


def test_retention_override_rejected_below_level_5(validator):
    # requisition is the only route a CD passes at level 4, isolating the
    # retention-override level check from the route permission check
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        requisition=True,
        retention_override=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.PERMISSION_DENIED


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


def test_requisition_allowed_for_cd_at_level_4(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        requisition=True,
    )

    assert result.allowed
    assert result.route_type == "requisition"


def test_requisition_rejected_for_non_cd(validator):
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        requisition=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.PERMISSION_DENIED


def test_requisition_rejected_below_level_4(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=3,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        requisition=True,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.DISASTER_LEVEL_TOO_LOW


def test_requisition_ignores_adjacency(validator):
    # Apex and Zion aren't adjacent, but requisition bypasses routing rules
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
        requisition=True,
        adjacent_surplus={"Warden": 999},
    )

    assert result.allowed
    assert result.transit_via is None


def test_qc_cannot_organize_transit_at_level_4(validator):
    result = validator.validate(
        user_role=UserRole.QC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.PERMISSION_DENIED


def test_lc_cannot_organize_transit_at_level_5_is_actually_allowed(validator):
    # LC keeps transit access at level 5 (matrix: LC, CD)
    result = validator.validate(
        user_role=UserRole.LC,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed


def test_cd_cannot_organize_transit_at_level_4(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=4,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert not result.allowed
    assert result.reason == ValidationReason.PERMISSION_DENIED


def test_cd_can_organize_transit_at_level_5(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Zion",
        disaster_level=5,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed


def test_any_role_can_request_direct_transfer_at_level_5(validator):
    result = validator.validate(
        user_role=UserRole.CD,
        source_quarter="Apex",
        destination_quarter="Echo",
        disaster_level=5,
        quantity=1,
        initial_quantity=12,
        available_quantity=12,
    )

    assert result.allowed
    assert result.route_type == "direct"


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
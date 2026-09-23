import pytest

from app.models.role import UserRole
from app.services.transfer_permissions import (
    TransferAction,
    TransferPermissionService,
)


@pytest.mark.parametrize(
    ("role", "level", "expected"),
    [
        # L1
        (UserRole.QC, 1, False),
        (UserRole.LC, 1, False),
        (UserRole.CD, 1, False),

        # L2
        (UserRole.QC, 2, False),
        (UserRole.LC, 2, False),
        (UserRole.CD, 2, False),

        # L3
        (UserRole.QC, 3, True),
        (UserRole.LC, 3, False),
        (UserRole.CD, 3, False),

        # L4
        (UserRole.QC, 4, True),
        (UserRole.LC, 4, True),
        (UserRole.CD, 4, False),

        # L5
        (UserRole.QC, 5, True),
        (UserRole.LC, 5, True),
        (UserRole.CD, 5, True),
    ],
)
def test_request_adjacent_transfer_permission(
    role: UserRole,
    level: int,
    expected: bool,
):
    result = TransferPermissionService.check(
        role=role,
        disaster_level=level,
        action=TransferAction.REQUEST_ADJACENT_TRANSFER,
    )

    assert result.allowed is expected


@pytest.mark.parametrize(
    ("role", "level", "expected"),
    [
        # L1
        (UserRole.QC, 1, False),
        (UserRole.LC, 1, False),
        (UserRole.CD, 1, False),

        # L2
        (UserRole.QC, 2, False),
        (UserRole.LC, 2, False),
        (UserRole.CD, 2, False),

        # L3
        (UserRole.QC, 3, False),
        (UserRole.LC, 3, False),
        (UserRole.CD, 3, False),

        # L4
        (UserRole.QC, 4, False),
        (UserRole.LC, 4, True),
        (UserRole.CD, 4, False),

        # L5
        (UserRole.QC, 5, False),
        (UserRole.LC, 5, True),
        (UserRole.CD, 5, True),
    ],
)
def test_organize_transit_permission(
    role: UserRole,
    level: int,
    expected: bool,
):
    result = TransferPermissionService.check(
        role=role,
        disaster_level=level,
        action=TransferAction.ORGANIZE_TRANSIT,
    )

    assert result.allowed is expected


@pytest.mark.parametrize(
    ("role", "level", "expected"),
    [
        # L1
        (UserRole.QC, 1, False),
        (UserRole.LC, 1, False),
        (UserRole.CD, 1, False),

        # L2
        (UserRole.QC, 2, False),
        (UserRole.LC, 2, False),
        (UserRole.CD, 2, False),

        # L3
        (UserRole.QC, 3, False),
        (UserRole.LC, 3, False),
        (UserRole.CD, 3, False),

        # L4
        (UserRole.QC, 4, False),
        (UserRole.LC, 4, False),
        (UserRole.CD, 4, True),

        # L5
        (UserRole.QC, 5, False),
        (UserRole.LC, 5, False),
        (UserRole.CD, 5, True),
    ],
)
def test_requisition_permission(
    role: UserRole,
    level: int,
    expected: bool,
):
    result = TransferPermissionService.check(
        role=role,
        disaster_level=level,
        action=TransferAction.REQUISITION,
    )

    assert result.allowed is expected


def test_invalid_disaster_level_is_rejected():
    result = TransferPermissionService.check(
        role=UserRole.CD,
        disaster_level=6,
        action=TransferAction.REQUISITION,
    )

    assert result.allowed is False
    assert result.message == "Invalid disaster level."


def test_denied_permission_contains_role_and_action():
    result = TransferPermissionService.check(
        role=UserRole.QC,
        disaster_level=4,
        action=TransferAction.REQUISITION,
    )

    assert result.allowed is False
    assert "QC" in result.message
    assert "REQUISITION" in result.message

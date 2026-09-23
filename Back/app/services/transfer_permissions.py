from enum import Enum

from app.models.role import UserRole


class TransferAction(str, Enum):
    REQUEST_ADJACENT_TRANSFER = "REQUEST_ADJACENT_TRANSFER"
    ORGANIZE_TRANSIT = "ORGANIZE_TRANSIT"
    REQUISITION = "REQUISITION"


class PermissionResult:
    def __init__(
        self,
        allowed: bool,
        message: str | None = None,
    ) -> None:
        self.allowed = allowed
        self.message = message


class TransferPermissionService:
    """
    Enforces the KAIJU permission matrix for transfer-related actions.

    Request adjacent transfer:
        L1: nobody
        L2: nobody
        L3: QC
        L4: QC + LC
        L5: QC + LC + CD

    Organize transit:
        L1: nobody
        L2: nobody
        L3: nobody
        L4: LC
        L5: LC + CD

    Requisition:
        L1: nobody
        L2: nobody
        L3: nobody
        L4: CD
        L5: CD
    """

    _PERMISSIONS: dict[
        TransferAction,
        dict[int, set[UserRole]],
    ] = {
        TransferAction.REQUEST_ADJACENT_TRANSFER: {
            1: set(),
            2: set(),
            3: {UserRole.QC},
            4: {UserRole.QC, UserRole.LC},
            5: {UserRole.QC, UserRole.LC, UserRole.CD},
        },
        TransferAction.ORGANIZE_TRANSIT: {
            1: set(),
            2: set(),
            3: set(),
            4: {UserRole.LC},
            5: {UserRole.LC, UserRole.CD},
        },
        TransferAction.REQUISITION: {
            1: set(),
            2: set(),
            3: set(),
            4: {UserRole.CD},
            5: {UserRole.CD},
        },
    }

    @classmethod
    def check(
        cls,
        *,
        role: UserRole,
        disaster_level: int,
        action: TransferAction,
    ) -> PermissionResult:
        if disaster_level not in {1, 2, 3, 4, 5}:
            return PermissionResult(
                allowed=False,
                message="Invalid disaster level.",
            )

        allowed_roles = cls._PERMISSIONS[action][disaster_level]

        if role in allowed_roles:
            return PermissionResult(allowed=True)

        return PermissionResult(
            allowed=False,
            message=(
                f"Role {role.value} is not allowed to perform "
                f"{action.value} at disaster level {disaster_level}."
            ),
        )
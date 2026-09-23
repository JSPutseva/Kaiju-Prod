from dataclasses import dataclass
from enum import Enum
from math import ceil

from app.models.role import UserRole


class ValidationReason(str, Enum):
    ALLOWED = "ALLOWED"

    INVALID_QUANTITY = "INVALID_QUANTITY"
    INVALID_QUARTER = "INVALID_QUARTER"
    SAME_QUARTER = "SAME_QUARTER"
    INVALID_RESOURCE_QUANTITY = "INVALID_RESOURCE_QUANTITY"

    DISASTER_LEVEL_TOO_LOW = "DISASTER_LEVEL_TOO_LOW"
    NON_ADJACENT_TRANSFER = "NON_ADJACENT_TRANSFER"
    MARITIME_NOT_ALLOWED = "MARITIME_NOT_ALLOWED"
    ADJACENT_SURPLUS_AVAILABLE = "ADJACENT_SURPLUS_AVAILABLE"
    INVALID_TRANSIT_QUARTER = "INVALID_TRANSIT_QUARTER"

    INSUFFICIENT_AVAILABLE_RESOURCE = "INSUFFICIENT_AVAILABLE_RESOURCE"
    RETENTION_LIMIT = "RETENTION_LIMIT"

    QC_APPROVAL_REQUIRED = "QC_APPROVAL_REQUIRED"


# retention floor: 30% of initial, rounded up (15% for CD at level 5)
def retention_min(initial_quantity: int, ratio: float = 0.30) -> int:
    return ceil(initial_quantity * ratio)


@dataclass(frozen=True)
class TransferValidationResult:
    allowed: bool
    reason: ValidationReason
    message: str | None = None
    route_type: str | None = None
    transit_via: str | None = None
    deprioritized_behind_xeno: bool = False


class TransferValidator:
    """
    Validates whether a resource transfer follows the KAIJU rules.

    Authentication and authorization are intentionally handled outside
    this service. The caller provides the authenticated user's role.
    """

    VALID_QUARTERS = {
        "Apex",
        "Echo",
        "Warden",
        "Xeno",
        "Zion",
    }

    LAND_CONNECTIONS = {
        frozenset(("Apex", "Echo")),
        frozenset(("Apex", "Warden")),
        frozenset(("Apex", "Xeno")),
        frozenset(("Echo", "Xeno")),
        frozenset(("Warden", "Xeno")),
        frozenset(("Warden", "Zion")),
        frozenset(("Xeno", "Zion")),
    }

    MARITIME_QUARTERS = {
        "Echo",
        "Xeno",
        "Zion",
    }

    def validate(
        self,
        *,
        user_role: UserRole,
        source_quarter: str,
        destination_quarter: str,
        disaster_level: int,
        quantity: int,
        initial_quantity: int,
        available_quantity: int,
        maritime: bool = False,
        transit_via: str | None = None,
        adjacent_surplus: dict[str, int] | None = None,
        qc_approved: bool = False,
        lc_approved: bool = False,
        cd_approved: bool = False,
    ) -> TransferValidationResult:

        # -------------------------
        # Basic validation
        # -------------------------

        if quantity <= 0:
            return self._reject(
                ValidationReason.INVALID_QUANTITY,
                "Quantity must be greater than zero.",
            )

        if initial_quantity < 0 or available_quantity < 0:
            return self._reject(
                ValidationReason.INVALID_RESOURCE_QUANTITY,
                "Resource quantities can't be negative.",
            )

        if available_quantity > initial_quantity:
            return self._reject(
                ValidationReason.INVALID_RESOURCE_QUANTITY,
                "Available quantity can't exceed the initial quantity.",
            )

        if source_quarter not in self.VALID_QUARTERS:
            return self._reject(
                ValidationReason.INVALID_QUARTER,
                f"'{source_quarter}' is not a Tokyork quarter.",
            )

        if destination_quarter not in self.VALID_QUARTERS:
            return self._reject(
                ValidationReason.INVALID_QUARTER,
                f"'{destination_quarter}' is not a Tokyork quarter.",
            )

        if source_quarter == destination_quarter:
            return self._reject(
                ValidationReason.SAME_QUARTER,
                "Source and destination must be different quarters.",
            )

        if disaster_level < 1 or disaster_level > 5:
            return self._reject(
                ValidationReason.DISASTER_LEVEL_TOO_LOW,
                "Disaster level must be between 1 and 5.",
            )

        # -------------------------
        # Resource availability
        # -------------------------

        if quantity > available_quantity:
            return self._reject(
                ValidationReason.INSUFFICIENT_AVAILABLE_RESOURCE,
                f"Only {available_quantity} available, {quantity} requested.",
            )

        # -------------------------
        # Disaster level
        # -------------------------

        # L1: monitoring only.
        # L2: reservations inside own quarter only.
        # No inter-quarter transfer is allowed before L3.
        if disaster_level < 3:
            return self._reject(
                ValidationReason.DISASTER_LEVEL_TOO_LOW,
                "Inter-quarter transfers require at least disaster level 3.",
            )

        # -------------------------
        # Route validation
        # -------------------------

        route_type: str | None = None
        transit_via_result: str | None = None
        deprioritized_behind_xeno = False

        if maritime:
            # Only Echo, Xeno and Zion have sea access.
            if (
                source_quarter not in self.MARITIME_QUARTERS
                or destination_quarter not in self.MARITIME_QUARTERS
            ):
                return self._reject(
                    ValidationReason.MARITIME_NOT_ALLOWED,
                    "Both quarters need sea access for a maritime transfer.",
                )

            route_type = "maritime"
        else:
            connection = frozenset(
                (source_quarter, destination_quarter)
            )

            if connection in self.LAND_CONNECTIONS:
                route_type = "direct"
            else:
                # L3 only permits direct adjacent transfers.
                if disaster_level == 3:
                    return self._reject(
                        ValidationReason.NON_ADJACENT_TRANSFER,
                        "Quarters are not adjacent; direct transfers require "
                        "disaster level 4 or higher.",
                    )

                # L4/L5 permit extended transfers, but a quarter adjacent to
                # the destination that already has surplus stock takes
                # priority over routing from a non-adjacent supplier.
                surplus_neighbors = sorted(
                    q for q, s in (adjacent_surplus or {}).items() if s > 0
                )
                if surplus_neighbors:
                    return self._reject(
                        ValidationReason.ADJACENT_SURPLUS_AVAILABLE,
                        f"Quarter(s) {', '.join(surplus_neighbors)} are "
                        "adjacent to the destination and already have "
                        "surplus stock; request from one of those first.",
                    )

                if transit_via is not None:
                    if not self._valid_transit(
                        source_quarter, destination_quarter, transit_via
                    ):
                        return self._reject(
                            ValidationReason.INVALID_TRANSIT_QUARTER,
                            f"'{transit_via}' is not adjacent to both "
                            f"{source_quarter} and {destination_quarter}.",
                        )
                    transit_via_result = transit_via
                else:
                    transit_via_result = self._pick_transit(
                        source_quarter, destination_quarter
                    )
                    if transit_via_result is None:
                        return self._reject(
                            ValidationReason.NON_ADJACENT_TRANSFER,
                            f"No quarter is adjacent to both "
                            f"{source_quarter} and {destination_quarter}; "
                            "no valid land route.",
                        )

                route_type = "transit"
                deprioritized_behind_xeno = transit_via_result == "Xeno"

        # -------------------------
        # Retention rule
        # -------------------------

        # Normal threshold: 30%.
        # L5 CD override: 15%.
        retention_percentage = (
            0.15
            if disaster_level == 5
            else 0.30
        )

        minimum_retention = retention_min(
            initial_quantity,
            retention_percentage,
        )

        remaining_quantity = available_quantity - quantity

        if remaining_quantity < minimum_retention:
            return self._reject(
                ValidationReason.RETENTION_LIMIT,
                f"Transferring {quantity} would leave {remaining_quantity}, "
                f"below the retention floor of {minimum_retention} "
                f"({retention_percentage:.0%} of {initial_quantity}).",
            )

        # -------------------------
        # L3 QC approval
        # -------------------------

        if disaster_level == 3 and not qc_approved:
            return self._reject(
                ValidationReason.QC_APPROVAL_REQUIRED,
                "A Quarter Coordinator must approve this transfer.",
            )

        # -------------------------
        # L4/L5
        # -------------------------

        # L4:
        # - Adjacent transfers are allowed.
        # - Extended/transit transfers are allowed.
        # - LC organizes transit chains.
        # - CD can requisition resources.
        #
        # L5:
        # - All transfers are unlocked.
        # - CD may reduce retention to 15%.
        #
        # Specific role permissions are enforced by the
        # authorization layer, not by this validation service.
        #
        # Both the destination (and the transit quarter, if any) still need
        # to give their own consent before the transfer actually happens —
        # this result only says the route itself is valid.

        return TransferValidationResult(
            allowed=True,
            reason=ValidationReason.ALLOWED,
            route_type=route_type,
            transit_via=transit_via_result,
            deprioritized_behind_xeno=deprioritized_behind_xeno,
        )

    @classmethod
    def neighbors(cls, quarter: str) -> set[str]:
        neighbors: set[str] = set()
        for connection in cls.LAND_CONNECTIONS:
            if quarter in connection:
                neighbors |= connection - {quarter}
        return neighbors

    @classmethod
    def _valid_transit(
        cls,
        source_quarter: str,
        destination_quarter: str,
        transit_quarter: str,
    ) -> bool:
        if transit_quarter in (source_quarter, destination_quarter):
            return False
        return (
            transit_quarter in cls.neighbors(source_quarter)
            and transit_quarter in cls.neighbors(destination_quarter)
        )

    @classmethod
    def _pick_transit(
        cls,
        source_quarter: str,
        destination_quarter: str,
    ) -> str | None:
        candidates = cls.neighbors(source_quarter) & cls.neighbors(destination_quarter)
        if not candidates:
            return None
        return min(candidates)

    @staticmethod
    def _reject(
        reason: ValidationReason,
        message: str,
    ) -> TransferValidationResult:
        return TransferValidationResult(
            allowed=False,
            reason=reason,
            message=message,
        )

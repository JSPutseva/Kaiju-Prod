from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.role import UserRole


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole | None
    quarter_ids: list[int] = []


class RoleAssignIn(BaseModel):
    role: UserRole
    quarter_ids: list[int] = []


class QuarterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    disaster_level: int
    sea_access: bool


class DisasterLevelSetIn(BaseModel):
    quarter_ids: list[int] = Field(min_length=1)
    level: int = Field(ge=1, le=5)


class DisasterLevelEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quarter_id: int
    level: int
    changed_by_id: int | None
    created_at: datetime


class ResourceTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class QuarterResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quarter_id: int
    resource_type_id: int
    resource_name: str
    initial_quantity: int
    available_quantity: int
    reserved_quantity: int
    retention_min: int


class RouteTransferIn(BaseModel):
    source_quarter_id: int
    destination_quarter_id: int
    resource_type_id: int
    quantity: int = Field(gt=0)
    prefer_maritime: bool = False
    transit_via: int | None = None
    requisition: bool = False
    retention_override: bool = False


class RouteDecisionOut(BaseModel):
    ok: bool
    route_type: str | None = None
    transit_via: int | None = None
    deprioritized_behind_xeno: bool = False
    reason: str | None = None
    message: str | None = None


class ResourceRequestCreate(BaseModel):
    source_quarter_id: int
    destination_quarter_id: int
    resource_type_id: int
    quantity: int = Field(gt=0)
    prefer_maritime: bool = False
    transit_via: int | None = None
    requisition: bool = False
    retention_override: bool = False


class ResourceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    source_quarter_id: int
    destination_quarter_id: int
    resource_type_id: int
    quantity: int
    requisition: bool
    route_type: str | None
    transit_via_id: int | None
    status: str
    rejection_reason: str | None
    decided_by_id: int | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class RequestDenyIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ReservationCreate(BaseModel):
    quarter_id: int
    resource_type_id: int
    quantity: int = Field(gt=0)
    start_at: datetime
    end_at: datetime


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quarter_id: int
    resource_type_id: int
    user_id: int
    quantity: int
    status: str
    start_at: datetime
    end_at: datetime
    created_at: datetime

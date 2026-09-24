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


class DisasterLevelOut(BaseModel):
    level: int
    code: str
    name: str
    description: str


class DisasterLevelUpdate(BaseModel):
    level: int = Field(ge=1, le=5)


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


class ResourceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_id: int
    source_quarter_id: int
    destination_quarter_id: int
    resource_type_id: int
    quantity: int
    status: str
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime


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
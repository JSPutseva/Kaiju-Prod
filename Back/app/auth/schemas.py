from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.role import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole | None = None
    quarter_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: UserRole | None
    quarter_id: int | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
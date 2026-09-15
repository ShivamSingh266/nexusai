from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    role: str = "applicant"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool


class AuthResponse(BaseModel):
    data: UserResponse
    meta: dict = {}
    model_version: str | None = None
    source_version: str = "backend-v1"
    generated_at: str | None = None
    warnings: list[str] = []
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
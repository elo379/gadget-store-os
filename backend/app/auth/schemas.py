from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    role_name: str = ""
    personnel_id: str | None = None
    is_owner: bool = False
    is_active: bool = True

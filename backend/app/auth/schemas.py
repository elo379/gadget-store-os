import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthenticatedUser(BaseModel):
    user_id: str
    email: EmailStr

    @property
    def id(self) -> uuid.UUID:
        return uuid.UUID(str(self.user_id))

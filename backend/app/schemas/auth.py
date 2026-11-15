import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models import Role


class LoginRequest(BaseModel):
    # Deliberately not validated as an email address: a malformed address is simply an
    # unknown one, and sign-in answers 401 for it like for any wrong credential.
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: Role
    organization_id: uuid.UUID | None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class LinkRedeem(BaseModel):
    token: str = Field(min_length=16, max_length=200)


class CodeRequest(BaseModel):
    phone: str = Field(min_length=3, max_length=32)


class CodeVerify(BaseModel):
    phone: str = Field(min_length=3, max_length=32)
    code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]


class DemoRoleOut(BaseModel):
    role: Role
    name: str


class DemoRoles(BaseModel):
    enabled: bool
    roles: list[DemoRoleOut] = []


class DemoLogin(BaseModel):
    role: Role


class CodeSent(BaseModel):
    sent: bool = True

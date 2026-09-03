from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.identity import RoleCode


class RegisterRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=180)
    organization_slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    sector: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=60)
    country: str = Field(default="GT", pattern=r"^[A-Z]{2}$")


class OrganizationOption(BaseModel):
    id: UUID
    name: str
    slug: str
    role_code: RoleCode


class LoginRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    password: str
    organization_id: UUID | None = None
    mfa_code: str | None = Field(default=None, pattern=r"^\d{6}$")


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
    mfa_required: bool = False
    organization_selection_required: bool = False
    organizations: list[OrganizationOption] = Field(default_factory=list)


class OrganizationSelectionRequest(BaseModel):
    organization_id: UUID


class PlatformOrganizationUpdate(BaseModel):
    is_active: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    is_active: bool
    mfa_enabled: bool
    is_superadmin: bool
    role_code: RoleCode | None = None
    organization_id: UUID | None = None
    organization_name: str | None = None


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    sector: str | None
    size: str | None
    country: str


class PlatformOrganizationResponse(OrganizationResponse):
    is_active: bool
    member_count: int


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    sector: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=60)
    country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")


class MembershipResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    role_code: RoleCode
    is_active: bool


class InviteMemberRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)
    full_name: str = Field(min_length=2, max_length=160)
    role_code: RoleCode


class UpdateRoleRequest(BaseModel):
    role_code: RoleCode


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaVerifyRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=320)


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)


class PasswordResetAccepted(BaseModel):
    message: str = "Si la cuenta existe, recibirá instrucciones para continuar."
    development_token: str | None = None


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    ip_address: str | None
    user_agent: str | None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    action: str
    resource_type: str
    resource_id: str | None
    result: str
    correlation_id: str | None
    created_at: datetime

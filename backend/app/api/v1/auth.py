from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.base import utc_now
from app.models.identity import (
    Membership,
    Organization,
    PasswordResetToken,
    RoleCode,
    Session,
    User,
)
from app.schemas.identity import (
    ChangePasswordRequest,
    LoginRequest,
    MfaSetupResponse,
    MfaVerifyRequest,
    OrganizationOption,
    OrganizationSelectionRequest,
    PasswordResetAccepted,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security.dependencies import Principal, get_principal
from app.security.mfa import generate_mfa_secret, provisioning_uri, verify_totp
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, hash_token, new_refresh_token
from app.services.audit import add_audit

router = APIRouter(prefix="/auth", tags=["autenticación"])
GENERIC_LOGIN_ERROR = "Credenciales inválidas o cuenta no disponible"


def _aware(value: datetime | None) -> datetime | None:
    return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        "refresh_token",
        token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=f"{settings.api_v1_prefix}/auth",
    )


async def _issue_tokens(
    db: AsyncSession,
    request: Request,
    response: Response,
    user: User,
    membership: Membership,
    replaced_session: Session | None = None,
) -> TokenResponse:
    refresh = new_refresh_token()
    session = Session(
        user_id=user.id,
        organization_id=membership.organization_id,
        refresh_token_hash=hash_token(refresh),
        expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:500] or None,
    )
    db.add(session)
    await db.flush()
    if replaced_session is not None:
        replaced_session.replaced_by_id = session.id
    add_audit(
        db,
        request,
        "auth.login",
        "session",
        "success",
        user_id=user.id,
        organization_id=membership.organization_id,
    )
    await db.commit()
    _set_refresh_cookie(response, refresh)
    return TokenResponse(
        access_token=create_access_token(user.id, membership.organization_id, membership.role_code),
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    email = payload.email.lower()
    duplicate_user = await db.scalar(select(User.id).where(User.email == email))
    duplicate_org = await db.scalar(
        select(Organization.id).where(Organization.slug == payload.organization_slug)
    )
    if duplicate_user is not None or duplicate_org is not None:
        raise HTTPException(status_code=409, detail="No fue posible completar el registro")
    user = User(
        email=email, full_name=payload.full_name, password_hash=hash_password(payload.password)
    )
    organization = Organization(
        name=payload.organization_name,
        slug=payload.organization_slug,
        sector=payload.sector,
        size=payload.size,
        country=payload.country,
    )
    db.add_all([user, organization])
    await db.flush()
    membership = Membership(
        user_id=user.id, organization_id=organization.id, role_code=RoleCode.ORG_ADMIN
    )
    db.add(membership)
    await db.flush()
    add_audit(
        db,
        request,
        "organization.create",
        "organization",
        "success",
        user_id=user.id,
        organization_id=organization.id,
        resource_id=str(organization.id),
    )
    return await _issue_tokens(db, request, response, user, membership)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user = await db.scalar(
        select(User)
        .options(selectinload(User.memberships))
        .where(User.email == payload.email.lower(), User.deleted_at.is_(None))
    )
    now = utc_now()
    locked_until = _aware(user.locked_until) if user is not None else None
    if user is None or not user.is_active or (locked_until is not None and locked_until > now):
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_max_attempts:
            user.locked_until = now + timedelta(minutes=settings.login_lock_minutes)
            user.failed_login_attempts = 0
        add_audit(db, request, "auth.login", "user", "failure", user_id=user.id)
        await db.commit()
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    active_memberships = [
        item for item in user.memberships if item.is_active and item.deleted_at is None
    ]
    if user.mfa_enabled and (
        not payload.mfa_code
        or not user.mfa_secret
        or not verify_totp(user.mfa_secret, payload.mfa_code)
    ):
        return TokenResponse(access_token="", expires_in=0, mfa_required=True)
    if payload.organization_id is None and len(active_memberships) > 1:
        organization_ids = [item.organization_id for item in active_memberships]
        organizations = {
            item.id: item
            for item in (
                await db.scalars(
                    select(Organization).where(
                        Organization.id.in_(organization_ids),
                        Organization.is_active.is_(True),
                        Organization.deleted_at.is_(None),
                    )
                )
            ).all()
        }
        options = [
            OrganizationOption(
                id=item.organization_id,
                name=organizations[item.organization_id].name,
                slug=organizations[item.organization_id].slug,
                role_code=item.role_code,
            )
            for item in active_memberships
            if item.organization_id in organizations
        ]
        if len(options) > 1:
            return TokenResponse(
                access_token="",
                expires_in=0,
                organization_selection_required=True,
                organizations=options,
            )
    membership = next(
        (
            item
            for item in active_memberships
            if payload.organization_id is None
            or item.organization_id == payload.organization_id
        ),
        None,
    )
    if membership is None:
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    selected_organization = await db.scalar(
        select(Organization).where(
            Organization.id == membership.organization_id,
            Organization.is_active.is_(True),
            Organization.deleted_at.is_(None),
        )
    )
    if selected_organization is None:
        raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
    user.failed_login_attempts = 0
    user.locked_until = None
    return await _issue_tokens(db, request, response, user, membership)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    response: Response,
    cookie_token: str | None = Cookie(default=None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token = cookie_token or payload.refresh_token
    if not token:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    old = await db.scalar(select(Session).where(Session.refresh_token_hash == hash_token(token)))
    expires_at = _aware(old.expires_at) if old is not None else None
    if old is None or old.revoked_at is not None or expires_at is None or expires_at <= utc_now():
        if old is not None and old.revoked_at is not None:
            await db.execute(
                update(Session)
                .where(Session.user_id == old.user_id, Session.revoked_at.is_(None))
                .values(revoked_at=utc_now())
            )
            await db.commit()
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    user = await db.scalar(
        select(User)
        .options(selectinload(User.memberships))
        .where(User.id == old.user_id, User.is_active.is_(True))
    )
    if user is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    membership = next(
        (
            item for item in user.memberships
            if item.is_active
            and item.deleted_at is None
            and (old.organization_id is None or item.organization_id == old.organization_id)
        ),
        None,
    )
    if membership is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    organization = await db.scalar(
        select(Organization).where(
            Organization.id == membership.organization_id,
            Organization.is_active.is_(True),
            Organization.deleted_at.is_(None),
        )
    )
    if organization is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
    old.revoked_at = utc_now()
    return await _issue_tokens(db, request, response, user, membership, replaced_session=old)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> None:
    if refresh_token:
        session = await db.scalar(
            select(Session).where(Session.refresh_token_hash == hash_token(refresh_token))
        )
        if session and session.revoked_at is None:
            session.revoked_at = utc_now()
            await db.commit()
    response.delete_cookie("refresh_token", path=f"{settings.api_v1_prefix}/auth")


@router.get("/me", response_model=UserResponse)
async def me(
    principal: Principal = Depends(get_principal), db: AsyncSession = Depends(get_db)
) -> UserResponse:
    organization_name = None
    if principal.organization_id is not None:
        organization_name = await db.scalar(
            select(Organization.name).where(Organization.id == principal.organization_id)
        )
    return UserResponse(
        id=principal.user.id,
        email=principal.user.email,
        full_name=principal.user.full_name,
        is_active=principal.user.is_active,
        mfa_enabled=principal.user.mfa_enabled,
        is_superadmin=principal.user.is_superadmin,
        role_code=principal.role,
        organization_id=principal.organization_id,
        organization_name=organization_name,
    )


@router.get("/organizations", response_model=list[OrganizationOption])
async def my_organizations(
    principal: Principal = Depends(get_principal), db: AsyncSession = Depends(get_db)
) -> list[OrganizationOption]:
    memberships = list(
        (
            await db.scalars(
                select(Membership)
                .options(selectinload(Membership.organization))
                .where(
                    Membership.user_id == principal.user.id,
                    Membership.is_active.is_(True),
                    Membership.deleted_at.is_(None),
                )
            )
        ).all()
    )
    return [
        OrganizationOption(
            id=item.organization_id,
            name=item.organization.name,
            slug=item.organization.slug,
            role_code=item.role_code,
        )
        for item in memberships
        if item.organization.is_active and item.organization.deleted_at is None
    ]


@router.post("/select-organization", response_model=TokenResponse)
async def select_organization(
    payload: OrganizationSelectionRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    membership = await db.scalar(
        select(Membership).where(
            Membership.user_id == principal.user.id,
            Membership.organization_id == payload.organization_id,
            Membership.is_active.is_(True),
            Membership.deleted_at.is_(None),
        )
    )
    organization = await db.scalar(
        select(Organization).where(
            Organization.id == payload.organization_id,
            Organization.is_active.is_(True),
            Organization.deleted_at.is_(None),
        )
    )
    if membership is None or organization is None:
        raise HTTPException(status_code=403, detail="Organización no disponible")
    return await _issue_tokens(db, request, response, principal.user, membership)


@router.post("/password-reset/request", response_model=PasswordResetAccepted)
async def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetAccepted:
    user = await db.scalar(
        select(User).where(User.email == payload.email.lower(), User.deleted_at.is_(None))
    )
    raw_token: str | None = None
    if user is not None and user.is_active:
        raw_token = new_refresh_token()
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=utc_now() + timedelta(minutes=30),
            )
        )
        add_audit(
            db,
            request,
            "auth.password.reset.request",
            "user",
            "success",
            user_id=user.id,
            resource_id=str(user.id),
        )
        await db.commit()
    return PasswordResetAccepted(
        development_token=raw_token if settings.app_env == "development" else None
    )


@router.post("/password-reset/confirm", status_code=204)
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    reset = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token))
    )
    expires_at = _aware(reset.expires_at) if reset is not None else None
    if reset is None or reset.used_at is not None or expires_at is None or expires_at <= utc_now():
        raise HTTPException(status_code=400, detail="Enlace inválido o vencido")
    user = await db.get(User, reset.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=400, detail="Enlace inválido o vencido")
    user.password_hash = hash_password(payload.new_password)
    reset.used_at = utc_now()
    await db.execute(
        update(Session)
        .where(Session.user_id == user.id, Session.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
    add_audit(
        db,
        request,
        "auth.password.reset.complete",
        "user",
        "success",
        user_id=user.id,
        resource_id=str(user.id),
    )
    await db.commit()


@router.post("/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, principal.user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    principal.user.password_hash = hash_password(payload.new_password)
    await db.execute(
        update(Session)
        .where(Session.user_id == principal.user.id, Session.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
    add_audit(
        db,
        request,
        "auth.password.change",
        "user",
        "success",
        user_id=principal.user.id,
        organization_id=principal.organization_id,
        resource_id=str(principal.user.id),
    )
    await db.commit()


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(
    principal: Principal = Depends(get_principal), db: AsyncSession = Depends(get_db)
) -> MfaSetupResponse:
    secret = generate_mfa_secret()
    principal.user.mfa_secret = secret
    principal.user.mfa_enabled = False
    await db.commit()
    return MfaSetupResponse(
        secret=secret, provisioning_uri=provisioning_uri(secret, principal.user.email)
    )


@router.post("/mfa/verify", status_code=204)
async def enable_mfa(
    payload: MfaVerifyRequest,
    principal: Principal = Depends(get_principal),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not principal.user.mfa_secret or not verify_totp(principal.user.mfa_secret, payload.code):
        raise HTTPException(status_code=400, detail="Código MFA inválido")
    principal.user.mfa_enabled = True
    await db.commit()

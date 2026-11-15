"""Sign-in and the current user (PDT section 10.1)."""

import logging
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.messages import GatewayDep
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Role, User
from app.schemas.auth import (
    CodeRequest,
    CodeSent,
    CodeVerify,
    DemoLogin,
    DemoRoleOut,
    DemoRoles,
    LinkRedeem,
    LoginRequest,
    LoginResponse,
    UserOut,
)
from app.services import login as passwordless
from app.services.messaging.greenapi import GatewayError

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Verified against when the email is unknown, so both failures take the same time.
_DUMMY_HASH = hash_password("not-a-real-password")


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, session: SessionDep) -> LoginResponse:
    user = session.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    password_ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    return LoginResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=get_settings().access_token_ttl_minutes * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


# --- Demo sign-in: choose a role, no password -------------------------------------------------

DEMO_DOMAIN = "demo.zira"
DEMO_ROLES = (Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER, Role.FARMER)


def demo_email(role: Role) -> str:
    return f"demo-{role.value.replace('_', '-')}@{DEMO_DOMAIN}"


def _demo_users(session) -> dict[Role, User]:
    rows = session.scalars(
        select(User).where(
            func.lower(User.email).in_([demo_email(r) for r in DEMO_ROLES]),
            User.is_active.is_(True),
        )
    )
    return {user.role: user for user in rows if user.email.lower() == demo_email(user.role)}


@router.get("/demo/roles", response_model=DemoRoles)
def demo_roles(session: SessionDep) -> DemoRoles:
    """The roles that can be entered without a password. Off (and empty) unless the server sets
    DEMO_ROLE_LOGIN and the demo accounts have been seeded."""
    if not get_settings().demo_role_login:
        return DemoRoles(enabled=False)
    users = _demo_users(session)
    roles = [DemoRoleOut(role=r, name=users[r].name) for r in DEMO_ROLES if r in users]
    return DemoRoles(enabled=bool(roles), roles=roles)


@router.post("/demo/login", response_model=LoginResponse)
def demo_login(body: DemoLogin, session: SessionDep) -> LoginResponse:
    """Sign in as the demo account of a role. Only the seeded demo accounts can be entered this
    way, never a real user, and only while DEMO_ROLE_LOGIN is on."""
    if not get_settings().demo_role_login:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not found")
    user = _demo_users(session).get(body.role)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail={"code": "demo_not_seeded"})
    return LoginResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=get_settings().access_token_ttl_minutes * 60,
        user=UserOut.model_validate(user),
    )


# --- Passwordless sign-in for farmers (a one-time link, or a code on WhatsApp) -----------------


def _farmer_session(user: User) -> LoginResponse:
    """A farmer who proved themselves with a link or a code stays signed in on that phone."""
    ttl = timedelta(days=get_settings().farmer_session_days)
    return LoginResponse(
        access_token=create_access_token(user.id, user.role.value, ttl=ttl),
        expires_in=int(ttl.total_seconds()),
        user=UserOut.model_validate(user),
    )


def _refused(code: str) -> HTTPException:
    # One answer for every failure, so nothing says which part was wrong.
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"code": code})


@router.post("/link/redeem", response_model=LoginResponse)
def redeem_link(body: LinkRedeem, session: SessionDep) -> LoginResponse:
    user = passwordless.redeem_link(session, body.token)
    if user is None:
        raise _refused("invalid_link")
    return _farmer_session(user)


@router.post("/code/request", response_model=CodeSent, status_code=status.HTTP_202_ACCEPTED)
def request_code(body: CodeRequest, session: SessionDep, gateway: GatewayDep) -> CodeSent:
    """Send a sign-in code to the farmer's WhatsApp. The answer is the same whether or not the
    number belongs to a farmer, so it cannot be used to find out who has an account."""
    if gateway is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail={"code": "code_unavailable"}
        )
    issued = passwordless.request_code(session, body.phone)
    if issued is not None:
        user, code = issued
        minutes = get_settings().login_code_ttl_minutes
        try:
            gateway.send_text(
                user.phone or "",
                f"Zira giriş kodunuz: {code}\nKod {minutes} dakika geçerlidir. "
                "Kodu kimseyle paylaşmayın.",
            )
        except GatewayError as error:
            log.warning("sign-in code was not sent: %s", error)
    return CodeSent()


@router.post("/code/verify", response_model=LoginResponse)
def verify_code(body: CodeVerify, session: SessionDep) -> LoginResponse:
    user = passwordless.verify_code(session, body.phone, body.code)
    if user is None:
        raise _refused("invalid_code")
    return _farmer_session(user)

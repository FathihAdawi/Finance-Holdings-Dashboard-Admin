"""Authentication state: registration, sign-in, session validation, sign-out.

Only hashed passwords and hashed session tokens are ever persisted, and neither
the password hash nor the raw session token is logged or rendered in the UI.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import logging
import re
import secrets

import reflex as rx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Portfolio, User, UserRole, UserSession

SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
_PBKDF2_ITERATIONS = 240_000
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]{2,}$")
GENERIC_CREDENTIALS_ERROR = "Invalid email or password."


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError) as e:
        logging.exception(f"Error verifying password: {e}")
        return False


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _password_problem(password: str) -> str:
    if len(password) < 10:
        return "Password must be at least 10 characters long."
    if not any(c.islower() for c in password):
        return "Password must include a lowercase letter."
    if not any(c.isupper() for c in password):
        return "Password must include an uppercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must include a number."
    return ""


class AuthState(rx.State):
    """Cookie-backed session state for the finance workbench."""

    auth_token: str = rx.Cookie(
        "",
        name="fw_session",
        path="/",
        max_age=SESSION_MAX_AGE_SECONDS,
        same_site="lax",
        secure=True,
    )

    user_email: str = ""
    display_name: str = ""
    role: str = ""
    is_authenticated: bool = False
    is_submitting: bool = False
    error_message: str = ""

    @rx.var
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    @rx.var
    def initials(self) -> str:
        source = self.display_name or self.user_email
        parts = [p for p in source.replace(".", " ").split(" ") if p]
        if not parts:
            return "—"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return f"{parts[0][0]}{parts[1][0]}".upper()

    @rx.var
    def role_label(self) -> str:
        return "Administrator" if self.is_admin else "Standard user"

    @rx.var
    def home_route(self) -> str:
        return "/admin" if self.is_admin else "/dashboard"

    def _clear_identity(self) -> None:
        self.auth_token = ""
        self.user_email = ""
        self.display_name = ""
        self.role = ""
        self.is_authenticated = False

    async def _load_session(self) -> bool:
        """Validate the cookie token; refresh last_seen_at when valid."""
        token = self.auth_token
        if not token:
            self._clear_identity()
            return False
        token_hash = _hash_token(token)
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    select(UserSession, User)
                    .join(User, User.id == UserSession.user_id)
                    .where(
                        UserSession.token_hash == token_hash,
                        UserSession.revoked_at.is_(None),
                        UserSession.expires_at > _utcnow(),
                        User.is_active.is_(True),
                    )
                )
            ).first()
            if row is None:
                self._clear_identity()
                return False
            session_row, user = row
            session_row.last_seen_at = _utcnow()
            await asession.commit()
            self.user_email = user.email
            self.display_name = user.display_name or user.email
            self.role = user.role.value
            self.is_authenticated = True
            return True

    async def _issue_session(self, asession, user_id: int) -> None:
        token = secrets.token_urlsafe(48)
        asession.add(
            UserSession(
                user_id=user_id,
                token_hash=_hash_token(token),
                expires_at=_utcnow()
                + datetime.timedelta(seconds=SESSION_MAX_AGE_SECONDS),
                user_agent=str(self.router.headers.user_agent or "")[:255],
            )
        )
        await asession.commit()
        self.auth_token = token

    @rx.event
    async def check_session(self):
        """Guard for protected pages: redirect unauthenticated visitors."""
        self.error_message = ""
        if not await self._load_session():
            return rx.redirect("/login")

    @rx.event
    async def require_user(self):
        """Any signed-in account — including administrators — may use /dashboard."""
        self.error_message = ""
        if not await self._load_session():
            return rx.redirect("/login")

    @rx.event
    async def require_admin(self):
        self.error_message = ""
        if not await self._load_session():
            return rx.redirect("/login")
        if self.role != UserRole.ADMIN.value:
            return rx.redirect("/dashboard")

    @rx.event
    async def redirect_if_authenticated(self):
        """Used on /login and /register and the landing route."""
        self.error_message = ""
        self.is_submitting = False
        if await self._load_session():
            return rx.redirect(
                "/admin" if self.role == UserRole.ADMIN.value else "/dashboard"
            )

    @rx.event
    async def entry_redirect(self):
        if await self._load_session():
            return rx.redirect(
                "/admin" if self.role == UserRole.ADMIN.value else "/dashboard"
            )
        return rx.redirect("/login")

    def _home_path(self) -> str:
        return "/admin" if self.role == UserRole.ADMIN.value else "/dashboard"

    @rx.event
    async def sign_in(self, form_data: dict):
        email = _normalize_email(form_data.get("email"))
        password = str(form_data.get("password", ""))
        self.error_message = ""
        if not email or not password:
            self.error_message = "Enter your email and password."
            return
        self.is_submitting = True
        yield
        async with rx.asession() as asession:
            user = (
                await asession.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if (
                user is None
                or not user.is_active
                or not verify_password(password, user.password_hash)
            ):
                self.is_submitting = False
                self.error_message = GENERIC_CREDENTIALS_ERROR
                return
            user.last_login_at = _utcnow()
            await self._issue_session(asession, user.id)
            self.user_email = user.email
            self.display_name = user.display_name or user.email
            self.role = user.role.value
            self.is_authenticated = True
        self.is_submitting = False
        yield rx.redirect(
            "/admin" if self.role == UserRole.ADMIN.value else "/dashboard"
        )

    @rx.event
    async def register(self, form_data: dict):
        email = _normalize_email(form_data.get("email"))
        display_name = str(form_data.get("display_name", "")).strip()
        password = str(form_data.get("password", ""))
        confirm = str(form_data.get("confirm_password", ""))
        self.error_message = ""

        if not _EMAIL_RE.match(email) or len(email) > 320:
            self.error_message = "Enter a valid email address."
            return
        if len(display_name) < 2 or len(display_name) > 120:
            self.error_message = "Display name must be 2–120 characters."
            return
        problem = _password_problem(password)
        if problem:
            self.error_message = problem
            return
        if password != confirm:
            self.error_message = "Passwords do not match."
            return

        self.is_submitting = True
        yield

        password_hash = hash_password(password)
        async with rx.asession() as asession:
            existing = (
                await asession.execute(
                    select(User.id).where(User.email == email)
                )
            ).first()
            if existing is not None:
                self.is_submitting = False
                self.error_message = (
                    "An account with that email already exists."
                )
                return

            admin_taken = (
                await asession.execute(
                    select(User.id).where(User.admin_claim.is_(True))
                )
            ).first()

            user = User(
                email=email,
                display_name=display_name,
                password_hash=password_hash,
                role=UserRole.ADMIN if admin_taken is None else UserRole.USER,
                admin_claim=True if admin_taken is None else None,
            )
            asession.add(user)
            try:
                await asession.flush()
            except IntegrityError:
                # Another registration won the bootstrap claim (or the email was
                # taken) concurrently; retry as a standard account.
                await asession.rollback()
                user = User(
                    email=email,
                    display_name=display_name,
                    password_hash=password_hash,
                    role=UserRole.USER,
                    admin_claim=None,
                )
                asession.add(user)
                try:
                    await asession.flush()
                except IntegrityError:
                    logging.exception("Unexpected error")
                    await asession.rollback()
                    self.is_submitting = False
                    self.error_message = (
                        "An account with that email already exists."
                    )
                    return

            asession.add(Portfolio(user_id=user.id))
            user.last_login_at = _utcnow()
            await self._issue_session(asession, user.id)
            self.user_email = user.email
            self.display_name = user.display_name
            self.role = user.role.value
            self.is_authenticated = True
        self.is_submitting = False
        yield rx.redirect(
            "/admin" if self.role == UserRole.ADMIN.value else "/dashboard"
        )

    @rx.event
    async def sign_out(self):
        token = self.auth_token
        self._clear_identity()
        if token:
            async with rx.asession() as asession:
                session_row = (
                    await asession.execute(
                        select(UserSession).where(
                            UserSession.token_hash == _hash_token(token),
                            UserSession.revoked_at.is_(None),
                        )
                    )
                ).scalar_one_or_none()
                if session_row is not None:
                    session_row.revoked_at = _utcnow()
                    await asession.commit()
        return rx.redirect("/login")

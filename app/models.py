"""Managed database schema for the finance holdings workbench.

Design notes (visual direction preserved for future UI phases):
    ledger-inspired typography, deep ink + warm ivory surfaces, restrained
    emerald/amber status accents, dense readable composition, portfolio
    allocation/performance charts as the centerpiece.

This module defines ONLY the schema. No queries, seeding, or UI live here.
"""

from __future__ import annotations

import datetime
import enum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    """Single declarative base shared by every model in the app."""


class UserRole(str, enum.Enum):
    """Role assignment. The first registered account claims ADMIN."""

    USER = "user"
    ADMIN = "admin"


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class User(Base):
    """An authenticated account. Passwords are never stored in plaintext."""

    __tablename__ = "app_user"
    __table_args__ = (
        # Normalized (lowercased, trimmed) email is the login identity.
        UniqueConstraint("email", name="uq_app_user_email"),
        # Atomic first-account administrator claim: `admin_claim` is NULL for
        # every account except the single bootstrap administrator, which sets
        # it to True. The unique index means a concurrent second insert of the
        # claim fails at the database level rather than racing in Python.
        UniqueConstraint("admin_claim", name="uq_app_user_admin_claim"),
        CheckConstraint(
            "admin_claim IS NULL OR admin_claim = true",
            name="ck_app_user_admin_claim_true",
        ),
        CheckConstraint("length(email) > 3", name="ck_app_user_email_len"),
        Index("ix_app_user_role", "role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=16),
        default=UserRole.USER,
    )
    admin_claim: Mapped[bool | None] = mapped_column(
        default=None, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio: Mapped["Portfolio | None"] = relationship(
        back_populates="user",
        init=False,
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        init=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserSession(Base):
    """Server-side session record. Only a hash of the token is persisted."""

    __tablename__ = "user_session"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_session_token_hash"),
        Index("ix_user_session_user_expires", "user_id", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True)
    )
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    user_agent: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="sessions", init=False)


class Portfolio(Base):
    """Exactly one portfolio per user (enforced by the unique user_id)."""

    __tablename__ = "portfolio"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_portfolio_user_id"),
        CheckConstraint(
            "length(base_currency) = 3", name="ck_portfolio_currency_len"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), default="My Portfolio")
    base_currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="portfolio", init=False)
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio",
        init=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AssetType(str, enum.Enum):
    EQUITY = "equity"
    ETF = "etf"
    BOND = "bond"
    CRYPTO = "crypto"
    CASH = "cash"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class Holding(Base):
    """A position owned through a portfolio (never directly by a user)."""

    __tablename__ = "holding"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_holding_quantity_positive"),
        CheckConstraint(
            "purchase_price >= 0", name="ck_holding_purchase_price"
        ),
        CheckConstraint("current_price >= 0", name="ck_holding_current_price"),
        Index("ix_holding_portfolio_symbol", "portfolio_id", "symbol"),
        Index("ix_holding_asset_type", "asset_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(24))
    name: Mapped[str] = mapped_column(String(160), default="")
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", native_enum=False, length=20),
        default=AssetType.EQUITY,
    )
    quantity: Mapped[float] = mapped_column(Numeric(20, 6), default=0)
    purchase_price: Mapped[float] = mapped_column(Numeric(20, 4), default=0)
    current_price: Mapped[float] = mapped_column(Numeric(20, 4), default=0)
    purchase_date: Mapped[datetime.date] = mapped_column(
        default_factory=lambda: _utcnow().date()
    )
    notes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio: Mapped["Portfolio"] = relationship(
        back_populates="holdings", init=False
    )

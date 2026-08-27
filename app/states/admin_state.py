"""Administrator state: aggregate oversight, user management and cross-account
holdings maintenance.

Every load and every mutation re-validates the caller's session token AND the
administrator role directly against the database. Password hashes and session
tokens are never selected into state.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, TypedDict

import reflex as rx
import reflex_xy
import xy
from sqlalchemy import func, select

from app.models import (
    AssetType,
    Holding,
    Portfolio,
    User,
    UserRole,
    UserSession,
)
from app.states.auth_state import AuthState, _hash_token, _utcnow
from app.states.portfolio_state import (
    ASSET_TYPE_COLORS,
    ASSET_TYPE_LABELS,
)

ADMIN_SORT_LABELS: dict[str, str] = {
    "value_desc": "Market value (high → low)",
    "value_asc": "Market value (low → high)",
    "return_desc": "Return % (high → low)",
    "symbol_asc": "Symbol (A → Z)",
    "user_asc": "Account (A → Z)",
    "date_desc": "Purchase date (newest)",
}

USER_SORT_LABELS: dict[str, str] = {
    "value_desc": "Portfolio value (high → low)",
    "holdings_desc": "Holdings (most first)",
    "name_asc": "Display name (A → Z)",
    "created_desc": "Newest accounts",
    "created_asc": "Oldest accounts",
}


class AdminUserRow(TypedDict):
    id: int
    display_name: str
    email: str
    role: str
    role_label: str
    is_active: bool
    status_label: str
    created_at: str
    last_login_at: str
    holding_count: int
    cost_basis: float
    market_value: float
    gain: float
    is_bootstrap: bool
    is_self: bool
    can_promote: bool
    can_demote: bool
    demote_reason: str


class AdminHoldingRow(TypedDict):
    id: int
    user_id: int
    portfolio_id: int
    user_name: str
    user_email: str
    symbol: str
    name: str
    asset_type: str
    asset_type_label: str
    quantity: float
    purchase_price: float
    current_price: float
    purchase_date: str
    cost_basis: float
    market_value: float
    gain: float
    return_pct: float


class AllocationSlice(TypedDict):
    label: str
    value: float
    pct: float
    color: str


_EMPTY_FIELD_ERRORS: dict[str, str] = {
    "symbol": "",
    "name": "",
    "asset_type": "",
    "quantity": "",
    "purchase_price": "",
    "current_price": "",
    "purchase_date": "",
}


class AdminState(rx.State):
    """Oversight data for administrators only."""

    is_loading: bool = False
    load_error: str = ""
    admin_user_id: int = 0

    users: list[AdminUserRow] = []
    holdings: list[AdminHoldingRow] = []

    total_users: int = 0
    active_users: int = 0
    admin_users: int = 0
    total_portfolios: int = 0
    total_holdings: int = 0
    total_cost_basis: float = 0.0
    total_market_value: float = 0.0

    # user management filters
    user_query: str = ""
    user_role_filter: str = "all"
    user_status_filter: str = "all"
    user_sort_by: str = "value_desc"

    # holdings inspection filters
    holding_query: str = ""
    holding_asset_filter: str = "all"
    holding_sort_by: str = "value_desc"

    # role change confirmation
    role_target_id: int = 0
    role_target_label: str = ""
    role_target_new_role: str = ""
    is_changing_role: bool = False
    role_error: str = ""

    # holding edit form
    form_open: bool = False
    editing_id: int = 0
    editing_owner: str = ""
    is_saving: bool = False
    form_error: str = ""
    field_errors: dict[str, str] = dict(_EMPTY_FIELD_ERRORS)

    form_symbol: str = ""
    form_name: str = ""
    form_asset_type: str = "equity"
    form_quantity: str = ""
    form_purchase_price: str = ""
    form_current_price: str = ""
    form_purchase_date: str = ""

    # holding delete confirmation
    delete_id: int = 0
    delete_label: str = ""
    is_deleting: bool = False

    # -------------------------------------------------------------- options
    @rx.var
    def asset_type_options(self) -> list[str]:
        return list(ASSET_TYPE_LABELS.keys())

    @rx.var
    def holding_sort_options(self) -> list[str]:
        return list(ADMIN_SORT_LABELS.keys())

    @rx.var
    def user_sort_options(self) -> list[str]:
        return list(USER_SORT_LABELS.keys())

    # ---------------------------------------------------------- aggregates
    @rx.var
    def total_gain(self) -> float:
        return self.total_market_value - self.total_cost_basis

    @rx.var
    def total_gain_is_positive(self) -> bool:
        return self.total_gain >= 0

    @rx.var
    def total_return_pct(self) -> float:
        if self.total_cost_basis <= 0:
            return 0.0
        return (
            (self.total_market_value - self.total_cost_basis)
            / self.total_cost_basis
            * 100.0
        )

    @rx.var
    def average_portfolio_value(self) -> float:
        if self.total_portfolios <= 0:
            return 0.0
        return self.total_market_value / self.total_portfolios

    @rx.var
    def standard_users(self) -> int:
        return max(self.total_users - self.admin_users, 0)

    @rx.var
    def has_users(self) -> bool:
        return len(self.users) > 0

    @rx.var
    def has_holdings(self) -> bool:
        return len(self.holdings) > 0

    # ------------------------------------------------------------- filtering
    @rx.var
    def filtered_users(self) -> list[AdminUserRow]:
        query = self.user_query.strip().lower()
        rows = [
            u
            for u in self.users
            if (
                self.user_role_filter == "all"
                or u["role"] == self.user_role_filter
            )
            and (
                self.user_status_filter == "all"
                or (self.user_status_filter == "active") == u["is_active"]
            )
            and (
                not query
                or query in u["email"].lower()
                or query in u["display_name"].lower()
            )
        ]
        key = self.user_sort_by
        if key == "value_desc":
            rows.sort(key=lambda u: u["market_value"], reverse=True)
        elif key == "holdings_desc":
            rows.sort(key=lambda u: u["holding_count"], reverse=True)
        elif key == "name_asc":
            rows.sort(key=lambda u: u["display_name"].lower())
        elif key == "created_desc":
            rows.sort(key=lambda u: u["created_at"], reverse=True)
        elif key == "created_asc":
            rows.sort(key=lambda u: u["created_at"])
        return rows

    @rx.var
    def filtered_user_count(self) -> int:
        return len(self.filtered_users)

    @rx.var
    def user_filters_active(self) -> bool:
        return (
            bool(self.user_query.strip())
            or self.user_role_filter != "all"
            or self.user_status_filter != "all"
        )

    @rx.var
    def filtered_holdings(self) -> list[AdminHoldingRow]:
        query = self.holding_query.strip().lower()
        rows = [
            h
            for h in self.holdings
            if (
                self.holding_asset_filter == "all"
                or h["asset_type"] == self.holding_asset_filter
            )
            and (
                not query
                or query in h["symbol"].lower()
                or query in h["name"].lower()
                or query in h["user_email"].lower()
                or query in h["user_name"].lower()
            )
        ]
        key = self.holding_sort_by
        if key == "value_desc":
            rows.sort(key=lambda h: h["market_value"], reverse=True)
        elif key == "value_asc":
            rows.sort(key=lambda h: h["market_value"])
        elif key == "return_desc":
            rows.sort(key=lambda h: h["return_pct"], reverse=True)
        elif key == "symbol_asc":
            rows.sort(key=lambda h: h["symbol"])
        elif key == "user_asc":
            rows.sort(key=lambda h: h["user_email"].lower())
        elif key == "date_desc":
            rows.sort(key=lambda h: h["purchase_date"], reverse=True)
        return rows

    @rx.var
    def filtered_holding_count(self) -> int:
        return len(self.filtered_holdings)

    @rx.var
    def holding_filters_active(self) -> bool:
        return (
            bool(self.holding_query.strip())
            or self.holding_asset_filter != "all"
        )

    @rx.var
    def allocation(self) -> list[AllocationSlice]:
        buckets: dict[str, float] = {}
        for h in self.holdings:
            buckets[h["asset_type"]] = (
                buckets.get(h["asset_type"], 0.0) + h["market_value"]
            )
        total = sum(buckets.values())
        rows: list[AllocationSlice] = []
        for asset_type, value in sorted(
            buckets.items(), key=lambda kv: kv[1], reverse=True
        ):
            if value <= 0:
                continue
            rows.append(
                {
                    "label": ASSET_TYPE_LABELS.get(asset_type, asset_type),
                    "value": value,
                    "pct": (value / total * 100.0) if total > 0 else 0.0,
                    "color": ASSET_TYPE_COLORS.get(asset_type, "#A8A090"),
                }
            )
        return rows

    # ---------------------------------------------------------------- charts
    @reflex_xy.figure
    def user_value_figure(self) -> xy.Chart:
        rows = sorted(
            self.users, key=lambda u: u["market_value"], reverse=True
        )[:10]
        rows = list(reversed(rows))
        labels = [
            (u["display_name"] or u["email"])[:22] or "—" for u in rows
        ] or ["No accounts"]
        values = [u["market_value"] for u in rows] or [0.0]
        costs = [u["cost_basis"] for u in rows] or [0.0]
        return xy.bar_chart(
            xy.bar(
                labels,
                costs,
                name="Cost basis",
                color="#C9C0AB",
                orientation="horizontal",
                opacity=1,
            ),
            xy.bar(
                labels,
                values,
                name="Market value",
                color="#1F5F4A",
                orientation="horizontal",
                opacity=1,
            ),
            xy.x_axis(label="USD"),
            xy.y_axis(label="Account"),
            xy.legend(),
            xy.modebar(show=False),
            xy.interaction_config(navigation=False),
            xy.theme(plot_background="#FFFDF8", text_color="#10231F"),
            height=320,
        )

    @reflex_xy.figure
    def allocation_figure(self) -> xy.Chart:
        rows = self.allocation
        if not rows:
            return xy.polar_bar_chart(
                xy.bar([180.0], [0.32], base=0.6, width=360.0, color="#DDD6C4"),
                xy.theta_axis(
                    unit="degrees",
                    zero="N",
                    show=False,
                    tick_label_strategy="none",
                ),
                xy.r_axis(
                    domain=(0.0, 1.0), show=False, tick_label_strategy="none"
                ),
                xy.legend(show=False),
                xy.modebar(show=False),
                xy.theme(plot_background="#FFFDF8", text_color="#10231F"),
                height=300,
            )
        widths = [r["pct"] / 100.0 * 360.0 for r in rows]
        angles: list[float] = []
        cursor = 0.0
        for w in widths:
            angles.append(cursor + w / 2.0)
            cursor += w
        return xy.polar_bar_chart(
            *(
                xy.bar(
                    [angle],
                    [0.32],
                    base=0.6,
                    width=width,
                    name=f"{row['label']} · {row['pct']:.1f}%",
                    color=row["color"],
                    opacity=1,
                    stroke="#FFFDF8",
                    stroke_width=3,
                )
                for row, angle, width in zip(rows, angles, widths, strict=True)
            ),
            xy.theta_axis(
                unit="degrees",
                zero="N",
                direction="counterclockwise",
                show=False,
                tick_label_strategy="none",
            ),
            xy.r_axis(
                domain=(0.0, 1.0), show=False, tick_label_strategy="none"
            ),
            xy.legend(show=False),
            xy.modebar(show=False),
            xy.theme(plot_background="#FFFDF8", text_color="#10231F"),
            height=300,
        )

    # ------------------------------------------------------- authorization
    async def _resolve_admin_id(self) -> int:
        """Re-validate the session AND the administrator role in the DB."""
        auth = await self.get_state(AuthState)
        token = auth.auth_token
        if not token:
            return 0
        async with rx.asession() as asession:
            row = (
                await asession.execute(
                    select(User.id)
                    .join(UserSession, UserSession.user_id == User.id)
                    .where(
                        UserSession.token_hash == _hash_token(token),
                        UserSession.revoked_at.is_(None),
                        UserSession.expires_at > _utcnow(),
                        User.is_active.is_(True),
                        User.role == UserRole.ADMIN,
                    )
                )
            ).first()
        return int(row[0]) if row is not None else 0

    # ------------------------------------------------------------- loading
    @rx.event
    async def load_overview(self):
        """Page on_load: aggregate counts, user roster and every holding."""
        self.is_loading = True
        self.load_error = ""
        yield
        admin_id = await self._resolve_admin_id()
        if admin_id == 0:
            self.is_loading = False
            self.users = []
            self.holdings = []
            self.load_error = (
                "Your administrator session is no longer valid. Sign in again."
            )
            return
        self.admin_user_id = admin_id
        try:
            async with rx.asession() as asession:
                # Per-user portfolio rollups in a single grouped query.
                totals_rows = (
                    await asession.execute(
                        select(
                            User.id,
                            User.email,
                            User.display_name,
                            User.role,
                            User.is_active,
                            User.admin_claim,
                            User.created_at,
                            User.last_login_at,
                            func.count(Holding.id),
                            func.coalesce(
                                func.sum(
                                    Holding.quantity * Holding.purchase_price
                                ),
                                0,
                            ),
                            func.coalesce(
                                func.sum(
                                    Holding.quantity * Holding.current_price
                                ),
                                0,
                            ),
                        )
                        .outerjoin(Portfolio, Portfolio.user_id == User.id)
                        .outerjoin(
                            Holding, Holding.portfolio_id == Portfolio.id
                        )
                        .group_by(User.id)
                    )
                ).all()

                portfolio_count = (
                    await asession.execute(select(func.count(Portfolio.id)))
                ).scalar_one()

                holding_rows = (
                    await asession.execute(
                        select(Holding, Portfolio, User)
                        .join(Portfolio, Portfolio.id == Holding.portfolio_id)
                        .join(User, User.id == Portfolio.user_id)
                    )
                ).all()
        except Exception as e:
            logging.exception(f"Error loading admin overview: {e}")
            self.is_loading = False
            self.load_error = (
                "Could not load oversight data. Refresh to try again."
            )
            return

        admin_count = sum(1 for row in totals_rows if row[3] == UserRole.ADMIN)
        users: list[AdminUserRow] = []
        total_cost = 0.0
        total_market = 0.0
        total_positions = 0
        active = 0
        for row in totals_rows:
            (
                user_id,
                email,
                display_name,
                role,
                is_active,
                admin_claim,
                created_at,
                last_login_at,
                count,
                cost,
                market,
            ) = row
            cost_f = float(cost or 0)
            market_f = float(market or 0)
            total_cost += cost_f
            total_market += market_f
            total_positions += int(count or 0)
            if is_active:
                active += 1
            is_admin = role == UserRole.ADMIN
            is_bootstrap = bool(admin_claim)
            is_self = int(user_id) == admin_id
            reason = ""
            if not is_admin:
                reason = ""
            elif is_bootstrap:
                reason = (
                    "Bootstrap administrator — this account cannot be demoted."
                )
            elif is_self:
                reason = "You cannot remove your own administrator role."
            elif admin_count <= 1:
                reason = "At least one administrator must remain."
            users.append(
                {
                    "id": int(user_id),
                    "display_name": display_name or email,
                    "email": email,
                    "role": role.value if is_admin else UserRole.USER.value,
                    "role_label": "Administrator"
                    if is_admin
                    else "Standard user",
                    "is_active": bool(is_active),
                    "status_label": "Active" if is_active else "Disabled",
                    "created_at": created_at.date().isoformat()
                    if created_at
                    else "—",
                    "last_login_at": last_login_at.date().isoformat()
                    if last_login_at
                    else "Never",
                    "holding_count": int(count or 0),
                    "cost_basis": cost_f,
                    "market_value": market_f,
                    "gain": market_f - cost_f,
                    "is_bootstrap": is_bootstrap,
                    "is_self": is_self,
                    "can_promote": not is_admin,
                    "can_demote": is_admin and reason == "",
                    "demote_reason": reason,
                }
            )

        self.users = users
        self.total_users = len(users)
        self.active_users = active
        self.admin_users = admin_count
        self.total_portfolios = int(portfolio_count or 0)
        self.total_holdings = total_positions
        self.total_cost_basis = total_cost
        self.total_market_value = total_market

        rows: list[AdminHoldingRow] = []
        for holding, portfolio, user in holding_rows:
            quantity = float(holding.quantity)
            purchase_price = float(holding.purchase_price)
            current_price = float(holding.current_price)
            cost_basis = quantity * purchase_price
            market_value = quantity * current_price
            gain = market_value - cost_basis
            rows.append(
                {
                    "id": int(holding.id),
                    "user_id": int(user.id),
                    "portfolio_id": int(portfolio.id),
                    "user_name": user.display_name or user.email,
                    "user_email": user.email,
                    "symbol": holding.symbol,
                    "name": holding.name,
                    "asset_type": holding.asset_type.value,
                    "asset_type_label": ASSET_TYPE_LABELS.get(
                        holding.asset_type.value, holding.asset_type.value
                    ),
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "current_price": current_price,
                    "purchase_date": holding.purchase_date.isoformat(),
                    "cost_basis": cost_basis,
                    "market_value": market_value,
                    "gain": gain,
                    "return_pct": (gain / cost_basis * 100.0)
                    if cost_basis > 0
                    else 0.0,
                }
            )
        self.holdings = rows
        self.is_loading = False

    # ------------------------------------------------------------- filters
    @rx.event
    def set_user_query(self, value: str):
        self.user_query = value

    @rx.event
    def set_user_role_filter(self, value: str):
        self.user_role_filter = value

    @rx.event
    def set_user_status_filter(self, value: str):
        self.user_status_filter = value

    @rx.event
    def set_user_sort_by(self, value: str):
        self.user_sort_by = value

    @rx.event
    def clear_user_filters(self):
        self.user_query = ""
        self.user_role_filter = "all"
        self.user_status_filter = "all"

    @rx.event
    def set_holding_query(self, value: str):
        self.holding_query = value

    @rx.event
    def set_holding_asset_filter(self, value: str):
        self.holding_asset_filter = value

    @rx.event
    def set_holding_sort_by(self, value: str):
        self.holding_sort_by = value

    @rx.event
    def clear_holding_filters(self):
        self.holding_query = ""
        self.holding_asset_filter = "all"

    # --------------------------------------------------------- role changes
    @rx.event
    def request_role_change(self, user_id: int, new_role: str):
        row = next((u for u in self.users if u["id"] == user_id), None)
        if row is None:
            return
        if new_role == UserRole.USER.value and not row["can_demote"]:
            self.role_error = row["demote_reason"]
            return
        self.role_error = ""
        self.role_target_id = user_id
        self.role_target_label = f"{row['display_name']} · {row['email']}"
        self.role_target_new_role = new_role

    @rx.event
    def cancel_role_change(self):
        self.role_target_id = 0
        self.role_target_label = ""
        self.role_target_new_role = ""
        self.is_changing_role = False

    @rx.event
    def dismiss_role_error(self):
        self.role_error = ""

    @rx.event
    async def confirm_role_change(self):
        if not self.role_target_id or not self.role_target_new_role:
            return
        self.is_changing_role = True
        self.role_error = ""
        yield
        admin_id = await self._resolve_admin_id()
        if admin_id == 0:
            self.is_changing_role = False
            self.role_target_id = 0
            self.role_error = (
                "Your administrator session expired. Sign in again."
            )
            return
        target_id = self.role_target_id
        new_role = self.role_target_new_role
        label = self.role_target_label
        async with rx.asession() as asession:
            target = (
                await asession.execute(select(User).where(User.id == target_id))
            ).scalar_one_or_none()
            if target is None:
                self.is_changing_role = False
                self.role_target_id = 0
                self.role_error = "That account no longer exists."
                return
            if new_role == UserRole.USER.value:
                if bool(target.admin_claim):
                    self.is_changing_role = False
                    self.role_target_id = 0
                    self.role_error = (
                        "The bootstrap administrator cannot be demoted."
                    )
                    return
                if target.id == admin_id:
                    self.is_changing_role = False
                    self.role_target_id = 0
                    self.role_error = (
                        "You cannot remove your own administrator role."
                    )
                    return
                admin_count = (
                    await asession.execute(
                        select(func.count(User.id)).where(
                            User.role == UserRole.ADMIN
                        )
                    )
                ).scalar_one()
                if int(admin_count or 0) <= 1:
                    self.is_changing_role = False
                    self.role_target_id = 0
                    self.role_error = "At least one administrator must remain."
                    return
                target.role = UserRole.USER
            else:
                target.role = UserRole.ADMIN
            try:
                await asession.commit()
            except Exception as e:
                logging.exception(f"Error changing role: {e}")
                await asession.rollback()
                self.is_changing_role = False
                self.role_target_id = 0
                self.role_error = "Could not update that role."
                return
        self.is_changing_role = False
        self.role_target_id = 0
        self.role_target_label = ""
        self.role_target_new_role = ""
        yield AdminState.load_overview
        yield rx.toast(
            f"Role updated for {label}.",
            duration=3500,
        )

    # ------------------------------------------------------- holding edits
    def _reset_field_errors(self) -> None:
        self.field_errors = dict(_EMPTY_FIELD_ERRORS)
        self.form_error = ""

    @rx.event
    def open_edit_form(self, holding_id: int):
        row = next((h for h in self.holdings if h["id"] == holding_id), None)
        if row is None:
            return
        self._reset_field_errors()
        self.editing_id = holding_id
        self.editing_owner = f"{row['user_name']} · {row['user_email']}"
        self.form_symbol = row["symbol"]
        self.form_name = row["name"]
        self.form_asset_type = row["asset_type"]
        self.form_quantity = f"{row['quantity']:g}"
        self.form_purchase_price = f"{row['purchase_price']:g}"
        self.form_current_price = f"{row['current_price']:g}"
        self.form_purchase_date = row["purchase_date"]
        self.form_open = True

    @rx.event
    def close_form(self):
        self.form_open = False
        self.is_saving = False
        self._reset_field_errors()

    @rx.event
    def set_form_asset_type(self, value: str):
        self.form_asset_type = value

    def _validate(self, form_data: dict[str, Any]) -> dict[str, str]:
        errors = dict(_EMPTY_FIELD_ERRORS)
        symbol = str(form_data.get("symbol", "")).strip().upper()
        name = str(form_data.get("name", "")).strip()
        asset_type = str(form_data.get("asset_type", "")).strip()
        if not symbol:
            errors["symbol"] = "Symbol is required."
        elif len(symbol) > 24:
            errors["symbol"] = "Symbol must be 24 characters or fewer."
        if not name:
            errors["name"] = "Name is required."
        elif len(name) > 160:
            errors["name"] = "Name must be 160 characters or fewer."
        if asset_type not in ASSET_TYPE_LABELS:
            errors["asset_type"] = "Choose an asset type."

        for field, label, allow_zero in (
            ("quantity", "Quantity", False),
            ("purchase_price", "Purchase price", True),
            ("current_price", "Current price", True),
        ):
            raw = str(form_data.get(field, "")).strip()
            if not raw:
                errors[field] = f"{label} is required."
                continue
            try:
                value = float(raw)
            except ValueError:
                errors[field] = f"{label} must be a number."
                continue
            if allow_zero and value < 0:
                errors[field] = f"{label} cannot be negative."
            elif not allow_zero and value <= 0:
                errors[field] = f"{label} must be greater than zero."

        raw_date = str(form_data.get("purchase_date", "")).strip()
        if not raw_date:
            errors["purchase_date"] = "Purchase date is required."
        else:
            try:
                parsed = datetime.date.fromisoformat(raw_date)
            except ValueError:
                errors["purchase_date"] = "Enter a valid date (YYYY-MM-DD)."
            else:
                if parsed > datetime.date.today():
                    errors["purchase_date"] = (
                        "Purchase date cannot be in the future."
                    )
                elif parsed.year < 1900:
                    errors["purchase_date"] = (
                        "Purchase date is too far in the past."
                    )
        return errors

    @rx.event
    async def save_holding(self, form_data: dict[str, Any]):
        errors = self._validate(form_data)
        self.field_errors = errors
        if any(errors.values()):
            self.form_error = "Fix the highlighted fields and try again."
            return
        self.form_error = ""
        self.is_saving = True
        yield

        row = next(
            (h for h in self.holdings if h["id"] == self.editing_id), None
        )
        if row is None:
            self.is_saving = False
            self.form_error = "That holding is no longer available."
            return

        admin_id = await self._resolve_admin_id()
        if admin_id == 0:
            self.is_saving = False
            self.form_error = (
                "Your administrator session expired. Sign in again."
            )
            return

        symbol = str(form_data.get("symbol", "")).strip().upper()
        name = str(form_data.get("name", "")).strip()
        asset_type = AssetType(
            str(form_data.get("asset_type", "equity")).strip()
        )
        quantity = float(str(form_data.get("quantity")).strip())
        purchase_price = float(str(form_data.get("purchase_price")).strip())
        current_price = float(str(form_data.get("current_price")).strip())
        purchase_date = datetime.date.fromisoformat(
            str(form_data.get("purchase_date")).strip()
        )

        async with rx.asession() as asession:
            holding = (
                await asession.execute(
                    select(Holding)
                    .join(Portfolio, Portfolio.id == Holding.portfolio_id)
                    .where(
                        Holding.id == self.editing_id,
                        # scoped by holding id AND the owning portfolio/account
                        Holding.portfolio_id == row["portfolio_id"],
                        Portfolio.user_id == row["user_id"],
                    )
                )
            ).scalar_one_or_none()
            if holding is None:
                self.is_saving = False
                self.form_error = "That holding is no longer available."
                return
            holding.symbol = symbol
            holding.name = name
            holding.asset_type = asset_type
            holding.quantity = quantity
            holding.purchase_price = purchase_price
            holding.current_price = current_price
            holding.purchase_date = purchase_date
            try:
                await asession.commit()
            except Exception as e:
                logging.exception(f"Error saving holding as admin: {e}")
                await asession.rollback()
                self.is_saving = False
                self.form_error = (
                    "Could not save this holding. Check the values."
                )
                return

        self.is_saving = False
        self.form_open = False
        self.editing_id = 0
        yield AdminState.load_overview
        yield rx.toast(f"{symbol} updated.", duration=3500)

    # ----------------------------------------------------- holding deletes
    @rx.event
    def request_delete(self, holding_id: int):
        row = next((h for h in self.holdings if h["id"] == holding_id), None)
        if row is None:
            return
        self.delete_id = holding_id
        self.delete_label = (
            f"{row['symbol']} — {row['name']} · {row['user_email']}"
        )

    @rx.event
    def cancel_delete(self):
        self.delete_id = 0
        self.delete_label = ""
        self.is_deleting = False

    @rx.event
    async def confirm_delete(self):
        if not self.delete_id:
            return
        row = next(
            (h for h in self.holdings if h["id"] == self.delete_id), None
        )
        if row is None:
            self.delete_id = 0
            return
        self.is_deleting = True
        yield
        admin_id = await self._resolve_admin_id()
        if admin_id == 0:
            self.is_deleting = False
            self.delete_id = 0
            self.load_error = (
                "Your administrator session expired. Sign in again."
            )
            return
        label = self.delete_label
        async with rx.asession() as asession:
            holding = (
                await asession.execute(
                    select(Holding)
                    .join(Portfolio, Portfolio.id == Holding.portfolio_id)
                    .where(
                        Holding.id == self.delete_id,
                        Holding.portfolio_id == row["portfolio_id"],
                        Portfolio.user_id == row["user_id"],
                    )
                )
            ).scalar_one_or_none()
            if holding is not None:
                await asession.delete(holding)
                await asession.commit()
        self.is_deleting = False
        self.delete_id = 0
        self.delete_label = ""
        yield AdminState.load_overview
        yield rx.toast(f"Deleted {label}.", duration=3500)

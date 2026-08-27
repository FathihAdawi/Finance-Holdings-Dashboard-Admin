"""Portfolio state: session-validated loading and mutation of the signed-in
user's own holdings. Every query and mutation is scoped to the portfolio that
belongs to the authenticated user resolved from the session token.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, TypedDict

import reflex as rx
import reflex_xy
import xy
from sqlalchemy import select

from app.models import AssetType, Holding, Portfolio, User, UserSession
from app.states.auth_state import AuthState, _hash_token, _utcnow

ASSET_TYPE_LABELS: dict[str, str] = {
    "equity": "Equity",
    "etf": "ETF",
    "bond": "Bond",
    "crypto": "Crypto",
    "cash": "Cash",
    "commodity": "Commodity",
    "real_estate": "Real estate",
    "other": "Other",
}

ASSET_TYPE_COLORS: dict[str, str] = {
    "equity": "#10231F",
    "etf": "#1F5F4A",
    "bond": "#3E7C63",
    "crypto": "#B45309",
    "cash": "#8A8272",
    "commodity": "#6B7C3E",
    "real_estate": "#4C5B7A",
    "other": "#A8A090",
}

SORT_LABELS: dict[str, str] = {
    "value_desc": "Market value (high → low)",
    "value_asc": "Market value (low → high)",
    "return_desc": "Return % (high → low)",
    "return_asc": "Return % (low → high)",
    "symbol_asc": "Symbol (A → Z)",
    "date_desc": "Purchase date (newest)",
    "date_asc": "Purchase date (oldest)",
}


class HoldingRow(TypedDict):
    id: int
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


class AllocationRow(TypedDict):
    label: str
    value: float
    pct: float
    color: str


class PortfolioState(rx.State):
    """Holdings workbench data for the signed-in user only."""

    portfolio_id: int = 0
    portfolio_name: str = "My Portfolio"
    holdings: list[HoldingRow] = []
    is_loading: bool = False
    load_error: str = ""

    search_query: str = ""
    asset_filter: str = "all"
    sort_by: str = "value_desc"

    form_open: bool = False
    form_mode: str = "create"
    editing_id: int = 0
    is_saving: bool = False
    form_error: str = ""
    field_errors: dict[str, str] = {
        "symbol": "",
        "name": "",
        "asset_type": "",
        "quantity": "",
        "purchase_price": "",
        "current_price": "",
        "purchase_date": "",
    }

    form_symbol: str = ""
    form_name: str = ""
    form_asset_type: str = "equity"
    form_quantity: str = ""
    form_purchase_price: str = ""
    form_current_price: str = ""
    form_purchase_date: str = ""

    delete_id: int = 0
    delete_label: str = ""
    is_deleting: bool = False

    # ----------------------------------------------------------------- reads
    @rx.var
    def asset_type_options(self) -> list[str]:
        return list(ASSET_TYPE_LABELS.keys())

    @rx.var
    def sort_options(self) -> list[str]:
        return list(SORT_LABELS.keys())

    @rx.var
    def sort_option_labels(self) -> list[str]:
        return list(SORT_LABELS.values())

    @rx.var
    def asset_type_option_labels(self) -> list[str]:
        return list(ASSET_TYPE_LABELS.values())

    @rx.var
    def holding_count(self) -> int:
        return len(self.holdings)

    @rx.var
    def has_holdings(self) -> bool:
        return len(self.holdings) > 0

    @rx.var
    def total_market_value(self) -> float:
        return sum(h["market_value"] for h in self.holdings)

    @rx.var
    def total_cost_basis(self) -> float:
        return sum(h["cost_basis"] for h in self.holdings)

    @rx.var
    def total_gain(self) -> float:
        return self.total_market_value - self.total_cost_basis

    @rx.var
    def total_return_pct(self) -> float:
        cost = self.total_cost_basis
        if cost <= 0:
            return 0.0
        return (self.total_market_value - cost) / cost * 100.0

    @rx.var
    def total_gain_is_positive(self) -> bool:
        return self.total_gain >= 0

    @rx.var
    def filtered_holdings(self) -> list[HoldingRow]:
        query = self.search_query.strip().lower()
        rows = [
            h
            for h in self.holdings
            if (
                self.asset_filter == "all"
                or h["asset_type"] == self.asset_filter
            )
            and (
                not query
                or query in h["symbol"].lower()
                or query in h["name"].lower()
                or query in h["asset_type_label"].lower()
            )
        ]
        key = self.sort_by
        if key == "value_desc":
            rows.sort(key=lambda h: h["market_value"], reverse=True)
        elif key == "value_asc":
            rows.sort(key=lambda h: h["market_value"])
        elif key == "return_desc":
            rows.sort(key=lambda h: h["return_pct"], reverse=True)
        elif key == "return_asc":
            rows.sort(key=lambda h: h["return_pct"])
        elif key == "symbol_asc":
            rows.sort(key=lambda h: h["symbol"])
        elif key == "date_desc":
            rows.sort(key=lambda h: h["purchase_date"], reverse=True)
        elif key == "date_asc":
            rows.sort(key=lambda h: h["purchase_date"])
        return rows

    @rx.var
    def filtered_count(self) -> int:
        return len(self.filtered_holdings)

    @rx.var
    def filters_active(self) -> bool:
        return bool(self.search_query.strip()) or self.asset_filter != "all"

    @rx.var
    def allocation(self) -> list[AllocationRow]:
        buckets: dict[str, float] = {}
        for h in self.holdings:
            buckets[h["asset_type"]] = (
                buckets.get(h["asset_type"], 0.0) + h["market_value"]
            )
        total = sum(buckets.values())
        rows: list[AllocationRow] = []
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

    @rx.var
    def best_position_label(self) -> str:
        if not self.holdings:
            return "—"
        best = max(self.holdings, key=lambda h: h["return_pct"])
        return f"{best['symbol']} {best['return_pct']:.1f}%"

    @rx.var
    def worst_position_label(self) -> str:
        if not self.holdings:
            return "—"
        worst = min(self.holdings, key=lambda h: h["return_pct"])
        return f"{worst['symbol']} {worst['return_pct']:.1f}%"

    # ---------------------------------------------------------------- charts
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
                height=280,
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
            height=280,
        )

    @reflex_xy.figure
    def cost_vs_market_figure(self) -> xy.Chart:
        rows = sorted(self.holdings, key=lambda h: h["purchase_date"])
        positions = list(range(1, len(rows) + 1))
        cost_series: list[float] = []
        market_series: list[float] = []
        running_cost = 0.0
        running_market = 0.0
        for row in rows:
            running_cost += row["cost_basis"]
            running_market += row["market_value"]
            cost_series.append(running_cost)
            market_series.append(running_market)
        if not positions:
            positions = [0]
            cost_series = [0.0]
            market_series = [0.0]
        return xy.chart(
            xy.line(
                positions,
                cost_series,
                name="Cumulative cost basis",
                color="#8A8272",
                width=2.5,
                dash="dashed",
            ),
            xy.line(
                positions,
                market_series,
                name="Cumulative market value",
                color="#1F5F4A",
                width=2.5,
            ),
            xy.x_axis(label="Positions, ordered by purchase date"),
            xy.y_axis(label="USD"),
            xy.legend(),
            xy.modebar(show=False),
            xy.interaction_config(navigation=False),
            xy.theme(plot_background="#FFFDF8", text_color="#10231F"),
            height=280,
        )

    # ------------------------------------------------------------ ownership
    async def _resolve_user_id(self) -> int:
        """Re-validate the session token and return the owning user id."""
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
                    )
                )
            ).first()
        return int(row[0]) if row is not None else 0

    def _row_from_holding(self, holding: Holding) -> HoldingRow:
        quantity = float(holding.quantity)
        purchase_price = float(holding.purchase_price)
        current_price = float(holding.current_price)
        cost_basis = quantity * purchase_price
        market_value = quantity * current_price
        gain = market_value - cost_basis
        return {
            "id": int(holding.id),
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

    @rx.event
    async def load_holdings(self):
        """Page on_load: fetch only this user's portfolio and holdings."""
        self.is_loading = True
        self.load_error = ""
        yield
        user_id = await self._resolve_user_id()
        if user_id == 0:
            self.is_loading = False
            self.holdings = []
            self.portfolio_id = 0
            return
        async with rx.asession() as asession:
            portfolio = (
                await asession.execute(
                    select(Portfolio).where(Portfolio.user_id == user_id)
                )
            ).scalar_one_or_none()
            if portfolio is None:
                portfolio = Portfolio(user_id=user_id)
                asession.add(portfolio)
                await asession.commit()
                await asession.refresh(portfolio)
            self.portfolio_id = int(portfolio.id)
            self.portfolio_name = portfolio.name
            rows = (
                (
                    await asession.execute(
                        select(Holding).where(
                            Holding.portfolio_id == portfolio.id
                        )
                    )
                )
                .scalars()
                .all()
            )
            self.holdings = [self._row_from_holding(h) for h in rows]
        self.is_loading = False

    # --------------------------------------------------------------- filters
    @rx.event
    def set_search_query(self, value: str):
        self.search_query = value

    @rx.event
    def set_asset_filter(self, value: str):
        self.asset_filter = value

    @rx.event
    def set_sort_by(self, value: str):
        self.sort_by = value

    @rx.event
    def clear_filters(self):
        self.search_query = ""
        self.asset_filter = "all"

    # ----------------------------------------------------------------- forms
    def _reset_field_errors(self) -> None:
        self.field_errors = {
            "symbol": "",
            "name": "",
            "asset_type": "",
            "quantity": "",
            "purchase_price": "",
            "current_price": "",
            "purchase_date": "",
        }
        self.form_error = ""

    @rx.event
    def open_create_form(self):
        self._reset_field_errors()
        self.form_mode = "create"
        self.editing_id = 0
        self.form_symbol = ""
        self.form_name = ""
        self.form_asset_type = "equity"
        self.form_quantity = ""
        self.form_purchase_price = ""
        self.form_current_price = ""
        self.form_purchase_date = datetime.date.today().isoformat()
        self.form_open = True

    @rx.event
    def open_edit_form(self, holding_id: int):
        self._reset_field_errors()
        row = next((h for h in self.holdings if h["id"] == holding_id), None)
        if row is None:
            return
        self.form_mode = "edit"
        self.editing_id = holding_id
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
        errors: dict[str, str] = {
            "symbol": "",
            "name": "",
            "asset_type": "",
            "quantity": "",
            "purchase_price": "",
            "current_price": "",
            "purchase_date": "",
        }
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
        notes = str(form_data.get("notes", "")).strip()[:500]

        user_id = await self._resolve_user_id()
        if user_id == 0:
            self.is_saving = False
            self.form_error = "Your session expired. Sign in again."
            return

        async with rx.asession() as asession:
            portfolio = (
                await asession.execute(
                    select(Portfolio).where(Portfolio.user_id == user_id)
                )
            ).scalar_one_or_none()
            if portfolio is None:
                portfolio = Portfolio(user_id=user_id)
                asession.add(portfolio)
                await asession.commit()
                await asession.refresh(portfolio)

            if self.form_mode == "edit" and self.editing_id:
                holding = (
                    await asession.execute(
                        select(Holding).where(
                            Holding.id == self.editing_id,
                            # ownership is enforced in the query itself
                            Holding.portfolio_id == portfolio.id,
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
                holding.notes = notes
            else:
                asession.add(
                    Holding(
                        portfolio_id=portfolio.id,
                        symbol=symbol,
                        name=name,
                        asset_type=asset_type,
                        quantity=quantity,
                        purchase_price=purchase_price,
                        current_price=current_price,
                        purchase_date=purchase_date,
                        notes=notes,
                    )
                )
            try:
                await asession.commit()
            except Exception as e:
                logging.exception(f"Error saving holding: {e}")
                await asession.rollback()
                self.is_saving = False
                self.form_error = (
                    "Could not save this holding. Check the values."
                )
                return

        self.is_saving = False
        self.form_open = False
        saved_symbol = symbol
        yield PortfolioState.load_holdings
        yield rx.toast(f"{saved_symbol} saved.", duration=3500)

    # -------------------------------------------------------------- deleting
    @rx.event
    def request_delete(self, holding_id: int):
        row = next((h for h in self.holdings if h["id"] == holding_id), None)
        if row is None:
            return
        self.delete_id = holding_id
        self.delete_label = f"{row['symbol']} — {row['name']}"

    @rx.event
    def cancel_delete(self):
        self.delete_id = 0
        self.delete_label = ""
        self.is_deleting = False

    @rx.event
    async def confirm_delete(self):
        if not self.delete_id:
            return
        self.is_deleting = True
        yield
        user_id = await self._resolve_user_id()
        if user_id == 0:
            self.is_deleting = False
            self.delete_id = 0
            return
        label = self.delete_label
        async with rx.asession() as asession:
            holding = (
                await asession.execute(
                    select(Holding)
                    .join(Portfolio, Portfolio.id == Holding.portfolio_id)
                    .where(
                        Holding.id == self.delete_id,
                        Portfolio.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if holding is not None:
                await asession.delete(holding)
                await asession.commit()
        self.is_deleting = False
        self.delete_id = 0
        self.delete_label = ""
        yield PortfolioState.load_holdings
        yield rx.toast(f"Deleted {label}.", duration=3500)

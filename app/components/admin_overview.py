"""Aggregate oversight strip: ledger totals plus the two centrepiece charts."""

import reflex as rx
import reflex_xy

from app.states.admin_state import AdminState, AllocationSlice


def _stat(label: str, value: rx.Var | str, note: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[#10231F]/50",
        ),
        rx.el.p(
            value,
            class_name="mt-2 font-serif text-2xl tabular-nums text-[#10231F]",
        ),
        rx.el.p(
            note, class_name="mt-1 font-mono text-[11px] text-[#10231F]/55"
        ),
        class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] px-4 py-4",
    )


def admin_totals() -> rx.Component:
    return rx.el.div(
        _stat(
            "Accounts",
            AdminState.total_users.to_string(),
            f"{AdminState.active_users} active · {AdminState.admin_users} admin",
        ),
        _stat(
            "Portfolios",
            AdminState.total_portfolios.to_string(),
            f"{AdminState.total_holdings} positions recorded",
        ),
        _stat(
            "Assets under book",
            f"${AdminState.total_market_value:,.2f}",
            f"Cost basis ${AdminState.total_cost_basis:,.2f}",
        ),
        rx.el.div(
            rx.el.p(
                "Aggregate gain / loss",
                class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[#10231F]/50",
            ),
            rx.el.p(
                f"${AdminState.total_gain:,.2f}",
                class_name=rx.cond(
                    AdminState.total_gain_is_positive,
                    "mt-2 font-serif text-2xl tabular-nums text-emerald-700",
                    "mt-2 font-serif text-2xl tabular-nums text-red-700",
                ),
            ),
            rx.el.p(
                f"{AdminState.total_return_pct:,.2f}% versus cost",
                class_name=rx.cond(
                    AdminState.total_gain_is_positive,
                    "mt-1 font-mono text-[11px] text-emerald-700",
                    "mt-1 font-mono text-[11px] text-red-700",
                ),
            ),
            class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] px-4 py-4",
        ),
        _stat(
            "Average portfolio",
            f"${AdminState.average_portfolio_value:,.2f}",
            f"{AdminState.standard_users} standard accounts",
        ),
        class_name="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5",
    )


def _panel_heading(title: str, note: str) -> rx.Component:
    return rx.el.div(
        rx.el.h2(title, class_name="font-serif text-lg text-[#10231F]"),
        rx.el.p(note, class_name="mt-1 text-xs text-[#10231F]/55"),
        class_name="border-b border-[#10231F]/15 pb-3",
    )


def _legend_row(row: AllocationSlice) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            class_name="size-2.5 shrink-0", style={"background": row["color"]}
        ),
        rx.el.span(
            row["label"], class_name="truncate text-sm text-[#10231F]/80"
        ),
        rx.el.span(
            f"{row['pct']:.1f}%",
            class_name="ml-auto font-mono text-xs tabular-nums text-[#10231F]/60",
        ),
        rx.el.span(
            f"${row['value']:,.0f}",
            class_name="w-24 text-right font-mono text-xs tabular-nums font-semibold text-[#10231F]",
        ),
        class_name="flex items-center gap-2 border-b border-[#10231F]/10 py-2 last:border-0",
    )


def user_value_panel() -> rx.Component:
    return rx.el.section(
        _panel_heading(
            "Portfolio value by account",
            "Ten largest books by market value, shown against the cost basis their owners recorded.",
        ),
        rx.cond(
            AdminState.has_users,
            rx.el.div(
                reflex_xy.chart(
                    AdminState.user_value_figure,
                    height="320px",
                    class_name="w-full min-w-[320px]",
                ),
                class_name="mt-4 w-full",
            ),
            rx.el.p(
                "No accounts have registered yet.",
                class_name="mt-6 text-sm text-[#10231F]/55",
            ),
        ),
        class_name="flex w-full flex-1 flex-col border border-[#10231F]/15 bg-[#FFFDF8] p-5",
    )


def aggregate_allocation_panel() -> rx.Component:
    return rx.el.section(
        _panel_heading(
            "Aggregate asset allocation",
            "Share of total market value by asset type across every portfolio.",
        ),
        rx.cond(
            AdminState.has_holdings,
            rx.el.div(
                rx.el.div(
                    reflex_xy.chart(
                        AdminState.allocation_figure,
                        height="300px",
                        class_name="w-full min-w-[280px]",
                    ),
                    rx.el.div(
                        rx.el.span(
                            f"${AdminState.total_market_value:,.0f}",
                            class_name="font-serif text-xl tabular-nums text-[#10231F]",
                        ),
                        rx.el.span(
                            "Assets under book",
                            class_name="font-mono text-[10px] uppercase tracking-[0.16em] text-[#10231F]/50",
                        ),
                        class_name="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-1",
                    ),
                    class_name="relative w-full",
                ),
                rx.el.div(
                    rx.foreach(AdminState.allocation, _legend_row),
                    class_name="mt-2 w-full border-t border-[#10231F]/15 pt-2",
                ),
                class_name="mt-4 w-full",
            ),
            rx.el.p(
                "Allocation appears once any account records a holding.",
                class_name="mt-6 text-sm text-[#10231F]/55",
            ),
        ),
        class_name="flex w-full flex-1 flex-col border border-[#10231F]/15 bg-[#FFFDF8] p-5",
    )


def admin_charts_row() -> rx.Component:
    return rx.el.div(
        user_value_panel(),
        aggregate_allocation_panel(),
        class_name="mt-5 flex w-full flex-col gap-5 lg:flex-row",
    )


def admin_skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="h-24 w-full animate-pulse bg-[#10231F]/10"),
        rx.el.div(class_name="h-64 w-full animate-pulse bg-[#10231F]/5"),
        rx.el.div(class_name="h-48 w-full animate-pulse bg-[#10231F]/10"),
        class_name="mt-6 flex w-full flex-col gap-4",
    )


def admin_load_error() -> rx.Component:
    return rx.el.div(
        rx.icon("triangle-alert", class_name="h-5 w-5 text-red-700"),
        rx.el.p(
            AdminState.load_error,
            role="alert",
            class_name="mt-2 text-sm text-red-700",
        ),
        rx.el.button(
            "Retry",
            type="button",
            on_click=AdminState.load_overview,
            class_name="mt-3 border border-red-700/40 px-3 py-1.5 text-xs font-semibold text-red-700 transition-colors hover:bg-red-700 hover:text-white",
        ),
        class_name="mt-6 flex w-full flex-col items-start border border-red-700/30 bg-red-500/5 p-5",
    )

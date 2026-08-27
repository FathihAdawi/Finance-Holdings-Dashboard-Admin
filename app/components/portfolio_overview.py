"""Ledger summary totals and the allocation / cost-versus-market charts."""

import reflex as rx
import reflex_xy

from app.states.portfolio_state import AllocationRow, PortfolioState


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


def summary_totals() -> rx.Component:
    return rx.el.div(
        _stat(
            "Market value",
            f"${PortfolioState.total_market_value:,.2f}",
            f"{PortfolioState.holding_count} positions held",
        ),
        _stat(
            "Cost basis",
            f"${PortfolioState.total_cost_basis:,.2f}",
            "Quantity × purchase price",
        ),
        rx.el.div(
            rx.el.p(
                "Unrealised gain / loss",
                class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-[#10231F]/50",
            ),
            rx.el.p(
                f"${PortfolioState.total_gain:,.2f}",
                class_name=rx.cond(
                    PortfolioState.total_gain_is_positive,
                    "mt-2 font-serif text-2xl tabular-nums text-emerald-700",
                    "mt-2 font-serif text-2xl tabular-nums text-red-700",
                ),
            ),
            rx.el.p(
                f"{PortfolioState.total_return_pct:,.2f}% versus cost",
                class_name=rx.cond(
                    PortfolioState.total_gain_is_positive,
                    "mt-1 font-mono text-[11px] text-emerald-700",
                    "mt-1 font-mono text-[11px] text-red-700",
                ),
            ),
            class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] px-4 py-4",
        ),
        _stat(
            "Position extremes",
            PortfolioState.best_position_label,
            f"Weakest: {PortfolioState.worst_position_label}",
        ),
        class_name="grid w-full grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4",
    )


def _allocation_legend_row(row: AllocationRow) -> rx.Component:
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


def _panel_heading(title: str, note: str) -> rx.Component:
    return rx.el.div(
        rx.el.h2(title, class_name="font-serif text-lg text-[#10231F]"),
        rx.el.p(note, class_name="mt-1 text-xs text-[#10231F]/55"),
        class_name="border-b border-[#10231F]/15 pb-3",
    )


def allocation_panel() -> rx.Component:
    return rx.el.section(
        _panel_heading(
            "Asset allocation",
            "Share of current market value by asset type.",
        ),
        rx.cond(
            PortfolioState.has_holdings,
            rx.el.div(
                rx.el.div(
                    reflex_xy.chart(
                        PortfolioState.allocation_figure,
                        height="280px",
                        class_name="w-full min-w-[280px]",
                    ),
                    rx.el.div(
                        rx.el.span(
                            f"${PortfolioState.total_market_value:,.0f}",
                            class_name="font-serif text-xl tabular-nums text-[#10231F]",
                        ),
                        rx.el.span(
                            "Market value",
                            class_name="font-mono text-[10px] uppercase tracking-[0.16em] text-[#10231F]/50",
                        ),
                        class_name="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-1",
                    ),
                    class_name="relative w-full",
                ),
                rx.el.div(
                    rx.foreach(
                        PortfolioState.allocation, _allocation_legend_row
                    ),
                    class_name="mt-2 w-full border-t border-[#10231F]/15 pt-2",
                ),
                class_name="mt-4 w-full",
            ),
            rx.el.p(
                "Allocation appears once you record a holding.",
                class_name="mt-6 text-sm text-[#10231F]/55",
            ),
        ),
        class_name="flex w-full flex-1 flex-col border border-[#10231F]/15 bg-[#FFFDF8] p-5",
    )


def cost_vs_market_panel() -> rx.Component:
    return rx.el.section(
        _panel_heading(
            "Cost versus market",
            "Cumulative cost basis and current market value, positions ordered by purchase date. No market history is implied — every point is derived from your own recorded prices.",
        ),
        rx.cond(
            PortfolioState.has_holdings,
            rx.el.div(
                reflex_xy.chart(
                    PortfolioState.cost_vs_market_figure,
                    height="280px",
                    class_name="w-full min-w-[300px]",
                ),
                rx.el.p(
                    f"Spread of ${PortfolioState.total_gain:,.2f} between what you paid and what the book is worth today.",
                    class_name="mt-3 border-t border-[#10231F]/15 pt-3 font-mono text-[11px] text-[#10231F]/60",
                ),
                class_name="mt-4 w-full",
            ),
            rx.el.p(
                "Add holdings with purchase dates to plot cost against market value.",
                class_name="mt-6 text-sm text-[#10231F]/55",
            ),
        ),
        class_name="flex w-full flex-1 flex-col border border-[#10231F]/15 bg-[#FFFDF8] p-5",
    )


def charts_row() -> rx.Component:
    return rx.el.div(
        allocation_panel(),
        cost_vs_market_panel(),
        class_name="mt-5 flex w-full flex-col gap-5 lg:flex-row",
    )

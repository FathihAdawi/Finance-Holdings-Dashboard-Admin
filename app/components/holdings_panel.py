"""Holdings ledger: search, asset-type filter, sorting, table and card views."""

import reflex as rx

from app.states.portfolio_state import (
    ASSET_TYPE_LABELS,
    SORT_LABELS,
    HoldingRow,
    PortfolioState,
)

_GAIN = "font-mono text-xs tabular-nums text-emerald-700"
_LOSS = "font-mono text-xs tabular-nums text-red-700"


def _asset_filter_option(value: str) -> rx.Component:
    return rx.el.option(
        rx.match(
            value,
            ("equity", "Equity"),
            ("etf", "ETF"),
            ("bond", "Bond"),
            ("crypto", "Crypto"),
            ("cash", "Cash"),
            ("commodity", "Commodity"),
            ("real_estate", "Real estate"),
            "Other",
        ),
        value=value,
    )


def _sort_option(value: str) -> rx.Component:
    return rx.el.option(
        rx.match(
            value,
            ("value_desc", "Market value (high → low)"),
            ("value_asc", "Market value (low → high)"),
            ("return_desc", "Return % (high → low)"),
            ("return_asc", "Return % (low → high)"),
            ("symbol_asc", "Symbol (A → Z)"),
            ("date_desc", "Purchase date (newest)"),
            "Purchase date (oldest)",
        ),
        value=value,
    )


def _select(label: str, children: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/50",
        ),
        rx.el.div(
            children,
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-[#10231F]/50",
            ),
            class_name="relative mt-1 w-full",
        ),
        class_name="flex w-full flex-col sm:w-52",
    )


def toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Search",
                html_for="holdings-search",
                class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/50",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[#10231F]/45",
                ),
                rx.el.input(
                    id="holdings-search",
                    placeholder="Symbol, name or asset type",
                    default_value=PortfolioState.search_query,
                    on_change=PortfolioState.set_search_query.debounce(400),
                    class_name="w-full border border-[#10231F]/25 bg-white py-2 pl-9 pr-3 text-sm text-[#10231F] placeholder:text-[#10231F]/35 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden",
                ),
                class_name="relative mt-1 w-full",
            ),
            class_name="flex w-full flex-col",
        ),
        _select(
            "Asset type",
            rx.el.select(
                rx.el.option("All asset types", value="all"),
                rx.foreach(
                    PortfolioState.asset_type_options, _asset_filter_option
                ),
                value=PortfolioState.asset_filter,
                on_change=PortfolioState.set_asset_filter,
                class_name="w-full appearance-none border border-[#10231F]/25 bg-white py-2 pl-3 pr-9 text-sm text-[#10231F] focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden",
            ),
        ),
        _select(
            "Sort by",
            rx.el.select(
                rx.foreach(PortfolioState.sort_options, _sort_option),
                value=PortfolioState.sort_by,
                on_change=PortfolioState.set_sort_by,
                class_name="w-full appearance-none border border-[#10231F]/25 bg-white py-2 pl-3 pr-9 text-sm text-[#10231F] focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden",
            ),
        ),
        class_name="flex w-full flex-col gap-3 border-b border-[#10231F]/15 pb-4 sm:flex-row sm:items-end",
    )


def _row_actions(row: HoldingRow) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("pencil", class_name="h-3.5 w-3.5"),
            rx.el.span("Edit", class_name="hidden lg:inline"),
            type="button",
            aria_label=f"Edit {row['symbol']}",
            on_click=lambda: PortfolioState.open_edit_form(row["id"]),
            class_name="flex items-center gap-1.5 border border-[#10231F]/20 px-2 py-1 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-3.5 w-3.5"),
            rx.el.span("Delete", class_name="hidden lg:inline"),
            type="button",
            aria_label=f"Delete {row['symbol']}",
            on_click=lambda: PortfolioState.request_delete(row["id"]),
            class_name="flex items-center gap-1.5 border border-red-700/30 px-2 py-1 text-xs font-medium text-red-700 transition-colors hover:bg-red-700 hover:text-white",
        ),
        class_name="flex items-center justify-end gap-2",
    )


def _th(icon: str, label: str, extra: str = "") -> rx.Component:
    return rx.el.th(
        rx.el.div(
            rx.icon(icon, class_name="h-3.5 w-3.5 text-[#10231F]/45"),
            rx.el.span(label),
            class_name=f"flex items-center gap-1.5 {extra}",
        ),
        scope="col",
        class_name="border-b border-[#10231F]/20 px-3 py-2 text-left font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-[#10231F]/55",
    )


def _table_row(row: HoldingRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["symbol"],
                class_name="font-mono text-sm font-semibold text-[#10231F]",
            ),
            rx.el.p(row["name"], class_name="text-xs text-[#10231F]/60"),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            rx.el.span(
                row["asset_type_label"],
                class_name="w-fit border border-[#10231F]/20 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-[#10231F]/70",
            ),
            class_name="px-3 py-2.5",
        ),
        rx.el.td(
            f"{row['quantity']:,.4f}",
            class_name="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['purchase_price']:,.2f}",
            class_name="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['current_price']:,.2f}",
            class_name="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['market_value']:,.2f}",
            class_name="px-3 py-2.5 text-right font-mono text-xs tabular-nums font-semibold text-[#10231F]",
        ),
        rx.el.td(
            rx.el.p(
                f"${row['gain']:,.2f}",
                class_name=rx.cond(row["gain"] >= 0, _GAIN, _LOSS),
            ),
            rx.el.p(
                f"{row['return_pct']:,.2f}%",
                class_name=rx.cond(
                    row["gain"] >= 0,
                    "font-mono text-[11px] tabular-nums text-emerald-700/80",
                    "font-mono text-[11px] tabular-nums text-red-700/80",
                ),
            ),
            class_name="px-3 py-2.5 text-right",
        ),
        rx.el.td(
            row["purchase_date"],
            class_name="px-3 py-2.5 text-right font-mono text-xs tabular-nums text-[#10231F]/60",
        ),
        rx.el.td(_row_actions(row), class_name="px-3 py-2.5"),
        class_name="border-b border-[#10231F]/10 odd:bg-[#FFFDF8] even:bg-[#F7F2E7] transition-colors hover:bg-emerald-500/5",
    )


def _card(row: HoldingRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    row["symbol"],
                    class_name="font-mono text-sm font-semibold text-[#10231F]",
                ),
                rx.el.p(row["name"], class_name="text-xs text-[#10231F]/60"),
                class_name="flex flex-col",
            ),
            rx.el.span(
                row["asset_type_label"],
                class_name="w-fit border border-[#10231F]/20 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-[#10231F]/70",
            ),
            class_name="flex items-start justify-between gap-3",
        ),
        rx.el.div(
            _card_stat("Quantity", f"{row['quantity']:,.4f}"),
            _card_stat("Purchase", f"${row['purchase_price']:,.2f}"),
            _card_stat("Current", f"${row['current_price']:,.2f}"),
            _card_stat("Market value", f"${row['market_value']:,.2f}"),
            class_name="mt-3 grid grid-cols-2 gap-2 border-t border-[#10231F]/10 pt-3",
        ),
        rx.el.div(
            rx.el.p(
                f"${row['gain']:,.2f} · {row['return_pct']:,.2f}%",
                class_name=rx.cond(row["gain"] >= 0, _GAIN, _LOSS),
            ),
            rx.el.p(
                row["purchase_date"],
                class_name="font-mono text-[11px] text-[#10231F]/55",
            ),
            class_name="mt-3 flex items-center justify-between border-t border-[#10231F]/10 pt-3",
        ),
        rx.el.div(_row_actions(row), class_name="mt-3"),
        class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] p-4",
    )


def _card_stat(label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
        ),
        rx.el.p(
            value,
            class_name="font-mono text-xs tabular-nums text-[#10231F]",
        ),
        class_name="flex flex-col",
    )


def _skeleton() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="h-10 w-full animate-pulse bg-[#10231F]/10"),
        rx.el.div(class_name="h-10 w-full animate-pulse bg-[#10231F]/5"),
        rx.el.div(class_name="h-10 w-full animate-pulse bg-[#10231F]/10"),
        rx.el.div(class_name="h-10 w-full animate-pulse bg-[#10231F]/5"),
        class_name="mt-4 flex w-full flex-col gap-2",
    )


def _empty_ledger() -> rx.Component:
    return rx.el.div(
        rx.icon("notebook-pen", class_name="h-6 w-6 text-emerald-700"),
        rx.el.h3(
            "Your ledger is empty",
            class_name="mt-3 font-serif text-lg text-[#10231F]",
        ),
        rx.el.p(
            "Record your first position — symbol, asset type, quantity, the price you paid and the price today.",
            class_name="mt-2 max-w-md text-sm text-[#10231F]/60",
        ),
        rx.el.button(
            rx.icon("plus", class_name="h-4 w-4"),
            "Add your first holding",
            type="button",
            on_click=PortfolioState.open_create_form,
            class_name="mt-4 flex items-center gap-2 bg-[#10231F] px-4 py-2 text-sm font-semibold text-[#F5F0E6] transition-colors hover:bg-emerald-800",
        ),
        class_name="flex w-full flex-col items-center justify-center border border-dashed border-[#10231F]/25 bg-[#FFFDF8] px-6 py-12 text-center",
    )


def _no_matches() -> rx.Component:
    return rx.el.div(
        rx.icon("search-x", class_name="h-5 w-5 text-[#10231F]/50"),
        rx.el.p(
            "No holdings match your search or filter.",
            class_name="mt-2 text-sm text-[#10231F]/65",
        ),
        rx.el.button(
            "Clear filters",
            type="button",
            on_click=PortfolioState.clear_filters,
            class_name="mt-3 border border-[#10231F]/25 px-3 py-1.5 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
        ),
        class_name="flex w-full flex-col items-center justify-center border border-dashed border-[#10231F]/25 bg-[#FFFDF8] px-6 py-10 text-center",
    )


def _ledger_views() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _th("tag", "Position"),
                        _th("layers", "Type"),
                        _th("hash", "Quantity", "justify-end"),
                        _th("receipt", "Purchase", "justify-end"),
                        _th("activity", "Current", "justify-end"),
                        _th("wallet", "Market value", "justify-end"),
                        _th("trending-up", "Return", "justify-end"),
                        _th("calendar", "Bought", "justify-end"),
                        _th("settings-2", "Actions", "justify-end"),
                    )
                ),
                rx.el.tbody(
                    rx.foreach(PortfolioState.filtered_holdings, _table_row)
                ),
                class_name="w-full table-auto border-collapse",
            ),
            class_name="mt-4 hidden w-full overflow-hidden overflow-x-auto border border-[#10231F]/15 lg:block",
        ),
        rx.el.div(
            rx.foreach(PortfolioState.filtered_holdings, _card),
            class_name="mt-4 grid w-full grid-cols-1 gap-3 md:grid-cols-2 lg:hidden",
        ),
        class_name="w-full",
    )


def holdings_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Holdings ledger",
                    class_name="font-serif text-lg text-[#10231F]",
                ),
                rx.el.p(
                    f"{PortfolioState.filtered_count} of {PortfolioState.holding_count} positions shown",
                    class_name="mt-1 font-mono text-[11px] text-[#10231F]/55",
                ),
                class_name="flex flex-col",
            ),
            rx.el.button(
                rx.icon("plus", class_name="h-4 w-4"),
                "Add holding",
                type="button",
                on_click=PortfolioState.open_create_form,
                class_name="flex w-fit items-center gap-2 bg-[#10231F] px-4 py-2 text-sm font-semibold text-[#F5F0E6] transition-colors hover:bg-emerald-800",
            ),
            class_name="flex flex-col items-start justify-between gap-3 pb-4 sm:flex-row sm:items-center",
        ),
        toolbar(),
        rx.cond(
            PortfolioState.is_loading,
            _skeleton(),
            rx.cond(
                PortfolioState.has_holdings,
                rx.cond(
                    PortfolioState.filtered_count > 0,
                    _ledger_views(),
                    rx.el.div(_no_matches(), class_name="mt-4 w-full"),
                ),
                rx.el.div(_empty_ledger(), class_name="mt-4 w-full"),
            ),
        ),
        class_name="mt-5 w-full border border-[#10231F]/15 bg-[#F5F0E6] p-5",
    )

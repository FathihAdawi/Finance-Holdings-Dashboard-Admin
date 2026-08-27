"""Cross-account holdings inspection with validated admin edit and delete."""

import reflex as rx

from app.states.admin_state import AdminHoldingRow, AdminState

_GAIN = "font-mono text-xs tabular-nums text-emerald-700"
_LOSS = "font-mono text-xs tabular-nums text-red-700"

_SELECT_CLASS = (
    "w-full appearance-none border border-[#10231F]/25 bg-white py-2 pl-3 pr-9 text-sm "
    "text-[#10231F] focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden"
)

_INPUT = (
    "mt-1 w-full border border-[#10231F]/25 bg-white px-3 py-2 text-sm text-[#10231F] "
    "placeholder:text-[#10231F]/35 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden"
)
_INPUT_ERROR = (
    "mt-1 w-full border border-red-600 bg-red-50/40 px-3 py-2 text-sm text-[#10231F] "
    "placeholder:text-[#10231F]/35 focus:border-red-700 focus:ring-1 focus:ring-red-700 outline-hidden"
)


def _asset_option(value: str) -> rx.Component:
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


def _holding_sort_option(value: str) -> rx.Component:
    return rx.el.option(
        rx.match(
            value,
            ("value_desc", "Market value (high → low)"),
            ("value_asc", "Market value (low → high)"),
            ("return_desc", "Return % (high → low)"),
            ("symbol_asc", "Symbol (A → Z)"),
            ("user_asc", "Account (A → Z)"),
            "Purchase date (newest)",
        ),
        value=value,
    )


def _select(label: str, children: rx.Component, width: str) -> rx.Component:
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
        class_name=f"flex w-full flex-col {width}",
    )


def _toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Search holdings",
                html_for="admin-holding-search",
                class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/50",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[#10231F]/45",
                ),
                rx.el.input(
                    id="admin-holding-search",
                    placeholder="Account, email, symbol or name",
                    default_value=AdminState.holding_query,
                    on_change=AdminState.set_holding_query.debounce(400),
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
                rx.foreach(AdminState.asset_type_options, _asset_option),
                value=AdminState.holding_asset_filter,
                on_change=AdminState.set_holding_asset_filter,
                class_name=_SELECT_CLASS,
            ),
            "sm:w-48",
        ),
        _select(
            "Sort by",
            rx.el.select(
                rx.foreach(
                    AdminState.holding_sort_options, _holding_sort_option
                ),
                value=AdminState.holding_sort_by,
                on_change=AdminState.set_holding_sort_by,
                class_name=_SELECT_CLASS,
            ),
            "sm:w-56",
        ),
        class_name="flex w-full flex-col gap-3 border-b border-[#10231F]/15 pb-4 sm:flex-row sm:items-end",
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


def _actions(row: AdminHoldingRow) -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("pencil", class_name="h-3.5 w-3.5"),
            rx.el.span("Edit", class_name="hidden xl:inline"),
            type="button",
            aria_label=f"Edit {row['symbol']} for {row['user_email']}",
            on_click=lambda: AdminState.open_edit_form(row["id"]),
            class_name="flex items-center gap-1.5 border border-[#10231F]/20 px-2 py-1 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="h-3.5 w-3.5"),
            rx.el.span("Delete", class_name="hidden xl:inline"),
            type="button",
            aria_label=f"Delete {row['symbol']} for {row['user_email']}",
            on_click=lambda: AdminState.request_delete(row["id"]),
            class_name="flex items-center gap-1.5 border border-red-700/30 px-2 py-1 text-xs font-medium text-red-700 transition-colors hover:bg-red-700 hover:text-white",
        ),
        class_name="flex items-center justify-end gap-2",
    )


def _holding_row(row: AdminHoldingRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["user_name"],
                class_name="text-sm font-semibold text-[#10231F]",
            ),
            rx.el.p(
                row["user_email"],
                class_name="font-mono text-[11px] text-[#10231F]/55",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
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
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            f"{row['quantity']:,.4f}",
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['purchase_price']:,.2f}",
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['current_price']:,.2f}",
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['market_value']:,.2f}",
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums font-semibold text-[#10231F]",
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
            class_name="px-3 py-2.5 text-right align-top",
        ),
        rx.el.td(
            row["purchase_date"],
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/60",
        ),
        rx.el.td(_actions(row), class_name="px-3 py-2.5 align-top"),
        class_name="border-b border-[#10231F]/10 odd:bg-[#FFFDF8] even:bg-[#F7F2E7] transition-colors hover:bg-emerald-500/5",
    )


def _card_stat(label: str, value: rx.Var | str) -> rx.Component:
    return rx.el.div(
        rx.el.p(
            label,
            class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
        ),
        rx.el.p(
            value, class_name="font-mono text-xs tabular-nums text-[#10231F]"
        ),
        class_name="flex flex-col",
    )


def _holding_card(row: AdminHoldingRow) -> rx.Component:
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
        rx.el.p(
            f"{row['user_name']} · {row['user_email']}",
            class_name="mt-2 font-mono text-[11px] text-[#10231F]/60",
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
        rx.el.div(_actions(row), class_name="mt-3"),
        class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] p-4",
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
            on_click=AdminState.clear_holding_filters,
            class_name="mt-3 border border-[#10231F]/25 px-3 py-1.5 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
        ),
        class_name="mt-4 flex w-full flex-col items-center justify-center border border-dashed border-[#10231F]/25 bg-[#FFFDF8] px-6 py-10 text-center",
    )


def _views() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _th("user", "Account"),
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
                    rx.foreach(AdminState.filtered_holdings, _holding_row)
                ),
                class_name="w-full table-auto border-collapse",
            ),
            class_name="mt-4 hidden w-full overflow-hidden overflow-x-auto border border-[#10231F]/15 lg:block",
        ),
        rx.el.div(
            rx.foreach(AdminState.filtered_holdings, _holding_card),
            class_name="mt-4 grid w-full grid-cols-1 gap-3 md:grid-cols-2 lg:hidden",
        ),
        class_name="w-full",
    )


def admin_holdings_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Holdings across every account",
                    class_name="font-serif text-lg text-[#10231F]",
                ),
                rx.el.p(
                    f"{AdminState.filtered_holding_count} of {AdminState.total_holdings} positions shown",
                    class_name="mt-1 font-mono text-[11px] text-[#10231F]/55",
                ),
                class_name="flex flex-col",
            ),
            rx.cond(
                AdminState.holding_filters_active,
                rx.el.button(
                    "Clear filters",
                    type="button",
                    on_click=AdminState.clear_holding_filters,
                    class_name="w-fit border border-[#10231F]/25 px-3 py-1.5 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-col items-start justify-between gap-3 pb-4 sm:flex-row sm:items-center",
        ),
        _toolbar(),
        rx.cond(
            AdminState.has_holdings,
            rx.cond(
                AdminState.filtered_holding_count > 0, _views(), _no_matches()
            ),
            rx.el.div(
                rx.icon("notebook-pen", class_name="h-6 w-6 text-emerald-700"),
                rx.el.h3(
                    "No positions recorded yet",
                    class_name="mt-3 font-serif text-lg text-[#10231F]",
                ),
                rx.el.p(
                    "Once any account records a holding it appears here for inspection.",
                    class_name="mt-2 max-w-md text-sm text-[#10231F]/60",
                ),
                class_name="mt-4 flex w-full flex-col items-center justify-center border border-dashed border-[#10231F]/25 bg-[#FFFDF8] px-6 py-12 text-center",
            ),
        ),
        class_name="mt-5 w-full border border-[#10231F]/15 bg-[#F5F0E6] p-5",
    )


# ------------------------------------------------------------------ modals
def _error(field: str) -> rx.Component:
    return rx.cond(
        AdminState.field_errors[field] != "",
        rx.el.p(
            AdminState.field_errors[field],
            role="alert",
            class_name="mt-1 font-mono text-[11px] text-red-700",
        ),
        rx.fragment(),
    )


def _field(field: str, label: str, control: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"admin-{field}",
            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/60",
        ),
        control,
        _error(field),
        class_name="flex w-full flex-col",
    )


def _text_input(
    field: str, placeholder: str, default: rx.Var, **props
) -> rx.Component:
    return rx.el.input(
        id=f"admin-{field}",
        name=field,
        placeholder=placeholder,
        default_value=default,
        key=f"admin-{AdminState.editing_id}-{field}",
        aria_invalid=AdminState.field_errors[field] != "",
        class_name=rx.cond(
            AdminState.field_errors[field] != "", _INPUT_ERROR, _INPUT
        ),
        **props,
    )


def _asset_select() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(AdminState.asset_type_options, _asset_option),
            id="admin-asset_type",
            name="asset_type",
            default_value=AdminState.form_asset_type,
            key=f"admin-{AdminState.editing_id}-asset_type",
            class_name=f"{_INPUT} appearance-none pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-3 top-4 h-4 w-4 text-[#10231F]/50",
        ),
        class_name="relative w-full",
    )


def admin_holding_form_modal() -> rx.Component:
    return rx.cond(
        AdminState.form_open,
        rx.el.div(
            rx.el.div(
                on_click=AdminState.close_form,
                class_name="absolute inset-0 bg-[#10231F]/55",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            "Administrator edit",
                            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-700",
                        ),
                        rx.el.h2(
                            "Amend holding",
                            class_name="mt-1 font-serif text-xl text-[#10231F]",
                        ),
                        rx.el.p(
                            AdminState.editing_owner,
                            class_name="mt-1 font-mono text-xs text-[#10231F]/60",
                        ),
                        class_name="flex flex-col",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        type="button",
                        aria_label="Close form",
                        on_click=AdminState.close_form,
                        class_name="border border-[#10231F]/20 p-2 text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
                    ),
                    class_name="flex items-start justify-between gap-4 border-b border-[#10231F]/15 pb-4",
                ),
                rx.el.form(
                    rx.cond(
                        AdminState.form_error != "",
                        rx.el.p(
                            AdminState.form_error,
                            role="alert",
                            class_name="mb-4 border border-red-600/40 bg-red-500/10 px-3 py-2 text-sm text-red-700",
                        ),
                        rx.fragment(),
                    ),
                    rx.el.div(
                        _field(
                            "symbol",
                            "Symbol",
                            _text_input(
                                "symbol",
                                "AAPL",
                                AdminState.form_symbol,
                                max_length=24,
                                auto_capitalize="characters",
                            ),
                        ),
                        _field("asset_type", "Asset type", _asset_select()),
                        class_name="grid grid-cols-1 gap-4 sm:grid-cols-2",
                    ),
                    rx.el.div(
                        _field(
                            "name",
                            "Name",
                            _text_input(
                                "name",
                                "Apple Inc.",
                                AdminState.form_name,
                                max_length=160,
                            ),
                        ),
                        class_name="mt-4 w-full",
                    ),
                    rx.el.div(
                        _field(
                            "quantity",
                            "Quantity",
                            _text_input(
                                "quantity",
                                "10",
                                AdminState.form_quantity,
                                type="number",
                                step="any",
                                min="0",
                            ),
                        ),
                        _field(
                            "purchase_price",
                            "Purchase price",
                            _text_input(
                                "purchase_price",
                                "0.00",
                                AdminState.form_purchase_price,
                                type="number",
                                step="any",
                                min="0",
                            ),
                        ),
                        _field(
                            "current_price",
                            "Current price",
                            _text_input(
                                "current_price",
                                "0.00",
                                AdminState.form_current_price,
                                type="number",
                                step="any",
                                min="0",
                            ),
                        ),
                        class_name="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3",
                    ),
                    rx.el.div(
                        _field(
                            "purchase_date",
                            "Purchase date",
                            _text_input(
                                "purchase_date",
                                "YYYY-MM-DD",
                                AdminState.form_purchase_date,
                                type="date",
                            ),
                        ),
                        class_name="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=AdminState.close_form,
                            class_name="border border-[#10231F]/25 px-4 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                        ),
                        rx.el.button(
                            rx.cond(
                                AdminState.is_saving,
                                "Saving…",
                                "Save changes",
                            ),
                            type="submit",
                            disabled=AdminState.is_saving,
                            class_name="bg-[#10231F] px-4 py-2 text-sm font-semibold text-[#F5F0E6] transition-colors hover:bg-emerald-800 disabled:opacity-60",
                        ),
                        class_name="mt-6 flex items-center justify-end gap-3 border-t border-[#10231F]/15 pt-4",
                    ),
                    on_submit=AdminState.save_holding,
                    class_name="mt-4 w-full",
                ),
                class_name="relative z-10 max-h-[92dvh] w-full max-w-2xl overflow-y-auto border border-[#10231F]/25 bg-[#F5F0E6] p-6",
            ),
            role="dialog",
            aria_modal="true",
            class_name="fixed inset-0 z-50 flex items-center justify-center p-4",
        ),
        rx.fragment(),
    )


def admin_delete_modal() -> rx.Component:
    return rx.cond(
        AdminState.delete_id > 0,
        rx.el.div(
            rx.el.div(
                on_click=AdminState.cancel_delete,
                class_name="absolute inset-0 bg-[#10231F]/55",
            ),
            rx.el.div(
                rx.el.h2(
                    "Delete this holding?",
                    class_name="font-serif text-xl text-[#10231F]",
                ),
                rx.el.p(
                    AdminState.delete_label,
                    class_name="mt-2 font-mono text-sm text-[#10231F]/70",
                ),
                rx.el.p(
                    "This removes the position from that account's ledger permanently.",
                    class_name="mt-3 text-sm text-[#10231F]/60",
                ),
                rx.el.div(
                    rx.el.button(
                        "Keep it",
                        type="button",
                        on_click=AdminState.cancel_delete,
                        class_name="border border-[#10231F]/25 px-4 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                    ),
                    rx.el.button(
                        rx.cond(AdminState.is_deleting, "Deleting…", "Delete"),
                        type="button",
                        disabled=AdminState.is_deleting,
                        on_click=AdminState.confirm_delete,
                        class_name="bg-red-700 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-red-800 disabled:opacity-60",
                    ),
                    class_name="mt-6 flex items-center justify-end gap-3 border-t border-[#10231F]/15 pt-4",
                ),
                class_name="relative z-10 w-full max-w-md border border-[#10231F]/25 bg-[#F5F0E6] p-6",
            ),
            role="dialog",
            aria_modal="true",
            class_name="fixed inset-0 z-50 flex items-center justify-center p-4",
        ),
        rx.fragment(),
    )

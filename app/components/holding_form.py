"""Modal form for creating and editing a holding, plus delete confirmation."""

import reflex as rx

from app.states.portfolio_state import PortfolioState


def _error(field: str) -> rx.Component:
    return rx.cond(
        PortfolioState.field_errors[field] != "",
        rx.el.p(
            PortfolioState.field_errors[field],
            id=f"{field}-error",
            role="alert",
            class_name="mt-1 font-mono text-[11px] text-red-700",
        ),
        rx.fragment(),
    )


def _field(
    field: str,
    label: str,
    input_component: rx.Component,
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=field,
            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/60",
        ),
        input_component,
        _error(field),
        class_name="flex w-full flex-col",
    )


_INPUT = (
    "mt-1 w-full border border-[#10231F]/25 bg-white px-3 py-2 text-sm text-[#10231F] "
    "placeholder:text-[#10231F]/35 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden"
)
_INPUT_ERROR = (
    "mt-1 w-full border border-red-600 bg-red-50/40 px-3 py-2 text-sm text-[#10231F] "
    "placeholder:text-[#10231F]/35 focus:border-red-700 focus:ring-1 focus:ring-red-700 outline-hidden"
)


def _text_input(
    field: str, placeholder: str, default: rx.Var, **props
) -> rx.Component:
    return rx.el.input(
        id=field,
        name=field,
        placeholder=placeholder,
        default_value=default,
        key=f"{PortfolioState.form_mode}-{PortfolioState.editing_id}-{field}",
        aria_invalid=PortfolioState.field_errors[field] != "",
        class_name=rx.cond(
            PortfolioState.field_errors[field] != "", _INPUT_ERROR, _INPUT
        ),
        **props,
    )


def _asset_type_option(value: str) -> rx.Component:
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
            ("other", "Other"),
            "Other",
        ),
        value=value,
    )


def _asset_type_select() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.foreach(PortfolioState.asset_type_options, _asset_type_option),
            id="asset_type",
            name="asset_type",
            default_value=PortfolioState.form_asset_type,
            key=f"{PortfolioState.form_mode}-{PortfolioState.editing_id}-asset_type",
            class_name=f"{_INPUT} appearance-none pr-9",
        ),
        rx.icon(
            "chevron-down",
            class_name="pointer-events-none absolute right-3 top-4 h-4 w-4 text-[#10231F]/50",
        ),
        class_name="relative w-full",
    )


def holding_form_modal() -> rx.Component:
    return rx.cond(
        PortfolioState.form_open,
        rx.el.div(
            rx.el.div(
                on_click=PortfolioState.close_form,
                class_name="absolute inset-0 bg-[#10231F]/55",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            rx.cond(
                                PortfolioState.form_mode == "edit",
                                "Edit position",
                                "New position",
                            ),
                            class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-700",
                        ),
                        rx.el.h2(
                            rx.cond(
                                PortfolioState.form_mode == "edit",
                                "Amend holding",
                                "Record a holding",
                            ),
                            class_name="mt-1 font-serif text-xl text-[#10231F]",
                        ),
                        class_name="flex flex-col",
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        type="button",
                        aria_label="Close form",
                        on_click=PortfolioState.close_form,
                        class_name="border border-[#10231F]/20 p-2 text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
                    ),
                    class_name="flex items-start justify-between gap-4 border-b border-[#10231F]/15 pb-4",
                ),
                rx.el.form(
                    rx.cond(
                        PortfolioState.form_error != "",
                        rx.el.p(
                            PortfolioState.form_error,
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
                                PortfolioState.form_symbol,
                                max_length=24,
                                auto_capitalize="characters",
                            ),
                        ),
                        _field(
                            "asset_type", "Asset type", _asset_type_select()
                        ),
                        class_name="grid grid-cols-1 gap-4 sm:grid-cols-2",
                    ),
                    _field(
                        "name",
                        "Name",
                        _text_input(
                            "name",
                            "Apple Inc.",
                            PortfolioState.form_name,
                            max_length=160,
                        ),
                    ),
                    rx.el.div(
                        _field(
                            "quantity",
                            "Quantity",
                            _text_input(
                                "quantity",
                                "10",
                                PortfolioState.form_quantity,
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
                                PortfolioState.form_purchase_price,
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
                                PortfolioState.form_current_price,
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
                                PortfolioState.form_purchase_date,
                                type="date",
                            ),
                        ),
                        class_name="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=PortfolioState.close_form,
                            class_name="border border-[#10231F]/25 px-4 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                        ),
                        rx.el.button(
                            rx.cond(
                                PortfolioState.is_saving,
                                "Saving…",
                                rx.cond(
                                    PortfolioState.form_mode == "edit",
                                    "Save changes",
                                    "Add holding",
                                ),
                            ),
                            type="submit",
                            disabled=PortfolioState.is_saving,
                            class_name="bg-[#10231F] px-4 py-2 text-sm font-semibold text-[#F5F0E6] transition-colors hover:bg-emerald-800 disabled:opacity-60",
                        ),
                        class_name="mt-6 flex items-center justify-end gap-3 border-t border-[#10231F]/15 pt-4",
                    ),
                    on_submit=PortfolioState.save_holding,
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


def delete_confirm_modal() -> rx.Component:
    return rx.cond(
        PortfolioState.delete_id > 0,
        rx.el.div(
            rx.el.div(
                on_click=PortfolioState.cancel_delete,
                class_name="absolute inset-0 bg-[#10231F]/55",
            ),
            rx.el.div(
                rx.el.h2(
                    "Delete this holding?",
                    class_name="font-serif text-xl text-[#10231F]",
                ),
                rx.el.p(
                    PortfolioState.delete_label,
                    class_name="mt-2 font-mono text-sm text-[#10231F]/70",
                ),
                rx.el.p(
                    "This removes the position from your ledger permanently.",
                    class_name="mt-3 text-sm text-[#10231F]/60",
                ),
                rx.el.div(
                    rx.el.button(
                        "Keep it",
                        type="button",
                        on_click=PortfolioState.cancel_delete,
                        class_name="border border-[#10231F]/25 px-4 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                    ),
                    rx.el.button(
                        rx.cond(
                            PortfolioState.is_deleting, "Deleting…", "Delete"
                        ),
                        type="button",
                        disabled=PortfolioState.is_deleting,
                        on_click=PortfolioState.confirm_delete,
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

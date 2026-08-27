import reflex as rx

from app.components.admin_holdings_panel import (
    admin_delete_modal,
    admin_holding_form_modal,
    admin_holdings_panel,
)
from app.components.admin_overview import (
    admin_charts_row,
    admin_load_error,
    admin_skeleton,
    admin_totals,
)
from app.components.admin_users_panel import (
    admin_users_panel,
    role_change_modal,
)
from app.components.workbench_header import workbench_page
from app.states.admin_state import AdminState


def _personal_ledger_link() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("chart-candlestick", class_name="h-4 w-4 text-emerald-700"),
            rx.el.p(
                "Your own portfolio lives separately from this console.",
                class_name="text-sm text-[#10231F]/70",
            ),
            class_name="flex items-center gap-2",
        ),
        rx.el.a(
            rx.icon("arrow-right", class_name="h-4 w-4"),
            "Open my dashboard",
            href="/dashboard",
            class_name="flex w-fit items-center gap-2 border border-[#10231F]/25 px-3 py-2 text-sm font-semibold text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
        ),
        class_name="mt-6 flex w-full flex-col items-start justify-between gap-3 border border-[#10231F]/15 bg-[#FFFDF8] px-4 py-3 sm:flex-row sm:items-center",
    )


def _loaded_body() -> rx.Component:
    return rx.el.div(
        admin_totals(),
        admin_charts_row(),
        admin_users_panel(),
        admin_holdings_panel(),
        role_change_modal(),
        admin_holding_form_modal(),
        admin_delete_modal(),
        class_name="w-full",
    )


def admin_body() -> rx.Component:
    return rx.el.div(
        _personal_ledger_link(),
        rx.cond(
            AdminState.is_loading,
            admin_skeleton(),
            rx.cond(
                AdminState.load_error != "",
                admin_load_error(),
                rx.el.div(_loaded_body(), class_name="mt-6 w-full"),
            ),
        ),
        class_name="w-full",
    )


def admin_page() -> rx.Component:
    return workbench_page(
        "Administrator",
        "Oversight console",
        "Aggregate assets, account roles and every recorded position across the workbench.",
        admin_body(),
    )

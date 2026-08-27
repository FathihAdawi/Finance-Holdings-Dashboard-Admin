import reflex as rx

from app.components.holding_form import delete_confirm_modal, holding_form_modal
from app.components.holdings_panel import holdings_panel
from app.components.portfolio_overview import charts_row, summary_totals
from app.components.workbench_header import workbench_page
from app.states.auth_state import AuthState
from app.states.portfolio_state import PortfolioState


def admin_link() -> rx.Component:
    return rx.cond(
        AuthState.is_admin,
        rx.el.a(
            rx.icon("shield-check", class_name="h-4 w-4"),
            "Administration desk",
            href="/admin",
            class_name="flex w-fit items-center gap-2 border border-amber-600/40 bg-amber-500/10 px-3 py-2 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-500/20",
        ),
        rx.fragment(),
    )


def dashboard_body() -> rx.Component:
    return rx.el.div(
        admin_link(),
        rx.cond(
            PortfolioState.is_loading,
            rx.el.div(
                rx.el.div(
                    class_name="h-24 w-full animate-pulse bg-[#10231F]/10"
                ),
                class_name="mt-5 w-full",
            ),
            rx.el.div(summary_totals(), class_name="mt-5 w-full"),
        ),
        charts_row(),
        holdings_panel(),
        holding_form_modal(),
        delete_confirm_modal(),
        class_name="mt-6 w-full",
    )


def dashboard_page() -> rx.Component:
    return workbench_page(
        "Holdings",
        PortfolioState.portfolio_name,
        "Your positions, valued from the prices you record. Cost basis and market value are calculated from your own entries — no external market history is assumed.",
        dashboard_body(),
    )

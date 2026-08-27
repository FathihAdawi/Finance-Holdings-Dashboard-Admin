import reflex as rx

from app.pages.admin import admin_page
from app.pages.dashboard import dashboard_page
from app.pages.login import login_page
from app.pages.register import register_page
from app.states.admin_state import AdminState
from app.states.auth_state import AuthState
from app.states.portfolio_state import PortfolioState


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.icon("chart-candlestick", class_name="h-6 w-6 text-emerald-700"),
            rx.el.h1(
                "Holdings Workbench",
                class_name="mt-4 font-serif text-2xl text-[#10231F]",
            ),
            rx.el.p(
                "Verifying your session…",
                class_name="mt-2 text-sm text-[#10231F]/60",
            ),
            class_name="flex min-h-dvh flex-col items-center justify-center text-center",
        ),
        class_name="font-['Inter'] min-h-dvh bg-[#F5F0E6]",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index, route="/", on_load=AuthState.entry_redirect)
app.add_page(
    login_page,
    route="/login",
    title="Sign in · Holdings Workbench",
    on_load=AuthState.redirect_if_authenticated,
)
app.add_page(
    register_page,
    route="/register",
    title="Register · Holdings Workbench",
    on_load=AuthState.redirect_if_authenticated,
)
app.add_page(
    dashboard_page,
    route="/dashboard",
    title="Dashboard · Holdings Workbench",
    on_load=[AuthState.require_user, PortfolioState.load_holdings],
)
app.add_page(
    admin_page,
    route="/admin",
    title="Admin · Holdings Workbench",
    on_load=[AuthState.require_admin, AdminState.load_overview],
)

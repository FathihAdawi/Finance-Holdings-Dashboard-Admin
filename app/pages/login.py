import reflex as rx

from app.components.auth_shell import (
    auth_shell,
    feedback,
    field,
    submit_button,
)
from app.states.auth_state import AuthState


def login_form() -> rx.Component:
    return rx.el.div(
        rx.el.form(
            field(
                "Email",
                "email",
                "email",
                "you@firm.com",
                auto_complete="email",
            ),
            field(
                "Password",
                "password",
                "password",
                "••••••••••",
                auto_complete="current-password",
            ),
            feedback(),
            submit_button("Sign in", "Signing in…"),
            on_submit=AuthState.sign_in,
            reset_on_submit=False,
        ),
        rx.el.p(
            "New to the workbench? ",
            rx.el.a(
                "Create an account",
                href="/register",
                class_name="font-semibold text-emerald-800 underline decoration-emerald-700/40 underline-offset-4 hover:decoration-emerald-700",
            ),
            class_name="mt-8 text-sm text-[#10231F]/70",
        ),
    )


def login_page() -> rx.Component:
    return auth_shell(
        "Account access",
        "Sign in to your ledger",
        "Enter your credentials to review portfolios, allocations and performance.",
        login_form(),
    )

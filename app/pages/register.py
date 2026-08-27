import reflex as rx

from app.components.auth_shell import (
    auth_shell,
    feedback,
    field,
    submit_button,
)
from app.states.auth_state import AuthState


def register_form() -> rx.Component:
    return rx.el.div(
        rx.el.form(
            field(
                "Display name",
                "display_name",
                "text",
                "A. Whitfield",
                auto_complete="name",
            ),
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
                helper="At least 10 characters with upper, lower and a number.",
                auto_complete="new-password",
            ),
            field(
                "Confirm password",
                "confirm_password",
                "password",
                "••••••••••",
                auto_complete="new-password",
            ),
            feedback(),
            submit_button("Create account", "Creating account…"),
            on_submit=AuthState.register,
            reset_on_submit=False,
        ),
        rx.el.p(
            "The first account registered becomes the administrator.",
            class_name="mt-6 border-l-2 border-emerald-700/50 pl-3 text-xs text-[#10231F]/60",
        ),
        rx.el.p(
            "Already registered? ",
            rx.el.a(
                "Sign in",
                href="/login",
                class_name="font-semibold text-emerald-800 underline decoration-emerald-700/40 underline-offset-4 hover:decoration-emerald-700",
            ),
            class_name="mt-4 text-sm text-[#10231F]/70",
        ),
    )


def register_page() -> rx.Component:
    return auth_shell(
        "Open an account",
        "Register your workbench",
        "Create credentials to track holdings, allocation and performance.",
        register_form(),
    )

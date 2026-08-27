"""Compact authenticated header: identity, role and sign-out. No sidebar."""

import reflex as rx

from app.states.auth_state import AuthState


def workbench_header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon(
                    "chart-candlestick", class_name="h-5 w-5 text-emerald-700"
                ),
                rx.el.span(
                    "Holdings Workbench",
                    class_name="font-serif text-lg text-[#10231F]",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.el.div(
                    AuthState.initials,
                    class_name="flex size-9 items-center justify-center rounded-full bg-[#10231F] font-mono text-xs text-[#F5F0E6]",
                ),
                rx.el.div(
                    rx.el.p(
                        AuthState.display_name,
                        class_name="text-sm font-semibold text-[#10231F]",
                    ),
                    rx.el.p(
                        AuthState.user_email,
                        class_name="font-mono text-xs text-[#10231F]/55",
                    ),
                    class_name="hidden sm:block leading-tight",
                ),
                rx.el.span(
                    AuthState.role_label,
                    class_name=rx.cond(
                        AuthState.is_admin,
                        "w-fit border border-amber-600/40 bg-amber-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-amber-700",
                        "w-fit border border-emerald-700/30 bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-widest text-emerald-800",
                    ),
                ),
                rx.el.button(
                    rx.icon("log-out", class_name="h-4 w-4"),
                    rx.el.span("Sign out", class_name="hidden sm:inline"),
                    on_click=AuthState.sign_out,
                    class_name="flex items-center gap-2 border border-[#10231F]/20 px-3 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6]",
                ),
                class_name="flex items-center gap-3",
            ),
            class_name="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-4",
        ),
        class_name="w-full border-b border-[#10231F]/15 bg-[#F5F0E6]",
    )


def workbench_page(
    eyebrow: str, title: str, subtitle: str, body: rx.Component
) -> rx.Component:
    return rx.el.main(
        workbench_header(),
        rx.el.div(
            rx.el.p(
                eyebrow,
                class_name="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700",
            ),
            rx.el.h1(
                title,
                class_name="mt-2 font-serif text-3xl text-[#10231F]",
            ),
            rx.el.p(subtitle, class_name="mt-2 text-sm text-[#10231F]/65"),
            rx.el.div(class_name="mt-6 h-px w-full bg-[#10231F]/15"),
            body,
            class_name="mx-auto w-full max-w-6xl flex-1 px-6 py-10",
        ),
        class_name="font-['Inter'] flex min-h-dvh w-full flex-col bg-[#F5F0E6] text-[#10231F]",
    )


def placeholder_panel(label: str, note: str, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-4 w-4 text-emerald-700"),
            rx.el.span(
                label,
                class_name="font-serif text-base text-[#10231F]",
            ),
            class_name="flex items-center gap-2 border-b border-[#10231F]/15 pb-3",
        ),
        rx.el.p(note, class_name="mt-3 text-sm text-[#10231F]/60"),
        class_name="w-full border border-[#10231F]/15 bg-white/60 p-5",
    )

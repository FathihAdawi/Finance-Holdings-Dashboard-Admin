"""Asymmetric editorial auth layout with a small ledger/portfolio motif."""

import reflex as rx

from app.states.auth_state import AuthState


def _ledger_row(label: str, value: str, accent: str) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            label,
            class_name="text-xs tracking-widest uppercase text-[#F5F0E6]/60",
        ),
        rx.el.span(value, class_name=accent),
        class_name="flex items-baseline justify-between border-b border-[#F5F0E6]/15 py-2.5",
    )


def ledger_motif() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("book-open-text", class_name="h-4 w-4 text-emerald-400"),
            rx.el.span(
                "Ledger",
                class_name="font-serif text-sm tracking-wide text-[#F5F0E6]",
            ),
            rx.el.span(
                "FY / OPEN",
                class_name="ml-auto text-[10px] tracking-widest uppercase text-amber-400",
            ),
            class_name="flex items-center gap-2 border-b border-[#F5F0E6]/25 pb-3",
        ),
        _ledger_row("Positions", "24", "font-mono text-sm text-[#F5F0E6]"),
        _ledger_row(
            "Allocation", "6 classes", "font-mono text-sm text-[#F5F0E6]"
        ),
        _ledger_row(
            "Unrealised", "+4.82%", "font-mono text-sm text-emerald-400"
        ),
        _ledger_row("Cash drag", "1.10%", "font-mono text-sm text-amber-400"),
        rx.el.div(
            rx.el.div(class_name="h-16 w-3 bg-emerald-500/70"),
            rx.el.div(class_name="h-10 w-3 bg-emerald-500/50"),
            rx.el.div(class_name="h-20 w-3 bg-[#F5F0E6]/70"),
            rx.el.div(class_name="h-8 w-3 bg-amber-500/70"),
            rx.el.div(class_name="h-14 w-3 bg-emerald-500/40"),
            rx.el.div(class_name="h-24 w-3 bg-[#F5F0E6]/40"),
            class_name="mt-6 flex items-end gap-2",
        ),
        class_name="w-full max-w-xs border border-[#F5F0E6]/20 p-5",
    )


def auth_shell(
    eyebrow: str, title: str, subtitle: str, form: rx.Component
) -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    rx.icon(
                        "chart-candlestick",
                        class_name="h-5 w-5 text-emerald-400",
                    ),
                    rx.el.span(
                        "Holdings Workbench",
                        class_name="font-serif text-lg text-[#F5F0E6]",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "A precise ledger for portfolios, allocations and performance.",
                    class_name="mt-6 max-w-sm text-sm leading-relaxed text-[#F5F0E6]/70",
                ),
                rx.el.div(ledger_motif(), class_name="mt-10"),
                class_name="hidden lg:flex lg:w-[42%] flex-col justify-center bg-[#10231F] p-12",
            ),
            rx.el.section(
                rx.el.div(
                    rx.el.p(
                        eyebrow,
                        class_name="text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-700",
                    ),
                    rx.el.h1(
                        title,
                        class_name="mt-3 font-serif text-3xl sm:text-4xl text-[#10231F]",
                    ),
                    rx.el.p(
                        subtitle,
                        class_name="mt-2 text-sm text-[#10231F]/65",
                    ),
                    rx.el.div(class_name="mt-6 h-px w-full bg-[#10231F]/15"),
                    form,
                    class_name="w-full max-w-md",
                ),
                class_name="flex flex-1 items-center justify-center px-6 py-12 sm:px-10",
            ),
            class_name="flex min-h-dvh w-full flex-col lg:flex-row",
        ),
        class_name="font-['Inter'] min-h-dvh bg-[#F5F0E6] text-[#10231F]",
    )


def field(
    label: str,
    name: str,
    input_type: str,
    placeholder: str,
    helper: str = "",
    auto_complete: str = "on",
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=f"auth-{name}",
            class_name="block text-[11px] font-semibold uppercase tracking-[0.14em] text-[#10231F]/70",
        ),
        rx.el.input(
            id=f"auth-{name}",
            name=name,
            type=input_type,
            placeholder=placeholder,
            required=True,
            auto_complete=auto_complete,
            class_name="mt-2 w-full border-0 border-b border-[#10231F]/25 bg-transparent px-0 py-2 font-mono text-sm text-[#10231F] placeholder:text-[#10231F]/35 focus:border-emerald-700 focus:outline-hidden",
        ),
        rx.cond(
            helper != "",
            rx.el.p(helper, class_name="mt-1 text-xs text-[#10231F]/50"),
            rx.fragment(),
        ),
        class_name="mt-6",
    )


def feedback() -> rx.Component:
    return rx.el.div(
        rx.cond(
            AuthState.error_message != "",
            rx.el.div(
                rx.icon(
                    "triangle-alert",
                    class_name="h-4 w-4 shrink-0 text-amber-700",
                ),
                rx.el.span(
                    AuthState.error_message,
                    class_name="text-sm font-medium text-[#10231F]",
                ),
                class_name="mt-6 flex items-start gap-2 border-l-2 border-amber-600 bg-amber-500/10 px-3 py-2",
            ),
            rx.fragment(),
        ),
        role="alert",
        aria_live="polite",
    )


def submit_button(label: str, pending_label: str) -> rx.Component:
    return rx.el.button(
        rx.cond(
            AuthState.is_submitting,
            rx.el.span(
                rx.spinner(class_name="text-[#F5F0E6]"),
                rx.el.span(pending_label),
                class_name="flex items-center justify-center gap-2",
            ),
            rx.el.span(
                rx.el.span(label),
                rx.icon("arrow-right", class_name="h-4 w-4"),
                class_name="flex items-center justify-center gap-2",
            ),
        ),
        type="submit",
        disabled=AuthState.is_submitting,
        aria_busy=AuthState.is_submitting,
        class_name="mt-8 w-full bg-[#10231F] px-5 py-3 text-sm font-semibold tracking-wide text-[#F5F0E6] transition-colors hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-60",
    )

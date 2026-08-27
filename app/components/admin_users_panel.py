"""Account roster: search, filters, ledger figures and guarded role changes."""

import reflex as rx

from app.states.admin_state import AdminState, AdminUserRow


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


_SELECT_CLASS = (
    "w-full appearance-none border border-[#10231F]/25 bg-white py-2 pl-3 pr-9 text-sm "
    "text-[#10231F] focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden"
)


def _user_sort_option(value: str) -> rx.Component:
    return rx.el.option(
        rx.match(
            value,
            ("value_desc", "Portfolio value (high → low)"),
            ("holdings_desc", "Holdings (most first)"),
            ("name_asc", "Display name (A → Z)"),
            ("created_desc", "Newest accounts"),
            "Oldest accounts",
        ),
        value=value,
    )


def _users_toolbar() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Search accounts",
                html_for="admin-user-search",
                class_name="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-[#10231F]/50",
            ),
            rx.el.div(
                rx.icon(
                    "search",
                    class_name="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[#10231F]/45",
                ),
                rx.el.input(
                    id="admin-user-search",
                    placeholder="Display name or email",
                    default_value=AdminState.user_query,
                    on_change=AdminState.set_user_query.debounce(400),
                    class_name="w-full border border-[#10231F]/25 bg-white py-2 pl-9 pr-3 text-sm text-[#10231F] placeholder:text-[#10231F]/35 focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 outline-hidden",
                ),
                class_name="relative mt-1 w-full",
            ),
            class_name="flex w-full flex-col",
        ),
        _select(
            "Role",
            rx.el.select(
                rx.el.option("All roles", value="all"),
                rx.el.option("Administrators", value="admin"),
                rx.el.option("Standard users", value="user"),
                value=AdminState.user_role_filter,
                on_change=AdminState.set_user_role_filter,
                class_name=_SELECT_CLASS,
            ),
            "sm:w-44",
        ),
        _select(
            "Status",
            rx.el.select(
                rx.el.option("All statuses", value="all"),
                rx.el.option("Active", value="active"),
                rx.el.option("Disabled", value="disabled"),
                value=AdminState.user_status_filter,
                on_change=AdminState.set_user_status_filter,
                class_name=_SELECT_CLASS,
            ),
            "sm:w-40",
        ),
        _select(
            "Sort by",
            rx.el.select(
                rx.foreach(AdminState.user_sort_options, _user_sort_option),
                value=AdminState.user_sort_by,
                on_change=AdminState.set_user_sort_by,
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


def _role_badge(row: AdminUserRow) -> rx.Component:
    return rx.el.div(
        rx.el.span(
            row["role_label"],
            class_name=rx.cond(
                row["role"] == "admin",
                "w-fit border border-amber-600/40 bg-amber-500/10 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-widest text-amber-700",
                "w-fit border border-emerald-700/30 bg-emerald-500/10 px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-widest text-emerald-800",
            ),
        ),
        rx.cond(
            row["is_bootstrap"],
            rx.el.span(
                "Bootstrap",
                class_name="w-fit border border-[#10231F]/25 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-[#10231F]/60",
            ),
            rx.fragment(),
        ),
        rx.cond(
            row["is_self"],
            rx.el.span(
                "You",
                class_name="w-fit border border-[#10231F]/25 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-[#10231F]/60",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-wrap items-center gap-1.5",
    )


def _role_actions(row: AdminUserRow) -> rx.Component:
    return rx.el.div(
        rx.cond(
            row["role"] == "admin",
            rx.el.div(
                rx.el.button(
                    rx.icon("shield-off", class_name="h-3.5 w-3.5"),
                    rx.el.span("Make standard", class_name="hidden xl:inline"),
                    type="button",
                    disabled=~row["can_demote"],
                    title=rx.cond(
                        row["can_demote"],
                        "Change this account to a standard user",
                        row["demote_reason"],
                    ),
                    aria_label=f"Demote {row['email']}",
                    on_click=lambda: AdminState.request_role_change(
                        row["id"], "user"
                    ),
                    class_name="flex items-center gap-1.5 border border-[#10231F]/25 px-2 py-1 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F] hover:text-[#F5F0E6] disabled:cursor-not-allowed disabled:opacity-45 disabled:hover:bg-transparent disabled:hover:text-[#10231F]",
                ),
                rx.cond(
                    row["can_demote"],
                    rx.fragment(),
                    rx.el.p(
                        row["demote_reason"],
                        class_name="mt-1 max-w-[16rem] font-mono text-[10px] leading-snug text-amber-700",
                    ),
                ),
                class_name="flex flex-col items-end",
            ),
            rx.el.button(
                rx.icon("shield-check", class_name="h-3.5 w-3.5"),
                rx.el.span("Make admin", class_name="hidden xl:inline"),
                type="button",
                title="Grant administrator access",
                aria_label=f"Promote {row['email']}",
                on_click=lambda: AdminState.request_role_change(
                    row["id"], "admin"
                ),
                class_name="flex items-center gap-1.5 border border-amber-600/40 px-2 py-1 text-xs font-medium text-amber-700 transition-colors hover:bg-amber-600 hover:text-white",
            ),
        ),
        class_name="flex items-center justify-end",
    )


def _user_row(row: AdminUserRow) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.p(
                row["display_name"],
                class_name="text-sm font-semibold text-[#10231F]",
            ),
            rx.el.p(
                row["email"],
                class_name="font-mono text-xs text-[#10231F]/60",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(_role_badge(row), class_name="px-3 py-2.5 align-top"),
        rx.el.td(
            rx.el.span(
                row["status_label"],
                class_name=rx.cond(
                    row["is_active"],
                    "w-fit border border-emerald-700/30 bg-emerald-500/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-emerald-800",
                    "w-fit border border-red-700/30 bg-red-500/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-red-700",
                ),
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            rx.el.p(
                row["created_at"],
                class_name="font-mono text-xs tabular-nums text-[#10231F]/75",
            ),
            rx.el.p(
                f"Last seen {row['last_login_at']}",
                class_name="font-mono text-[10px] text-[#10231F]/50",
            ),
            class_name="px-3 py-2.5 align-top",
        ),
        rx.el.td(
            row["holding_count"].to_string(),
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            f"${row['cost_basis']:,.2f}",
            class_name="px-3 py-2.5 text-right align-top font-mono text-xs tabular-nums text-[#10231F]/80",
        ),
        rx.el.td(
            rx.el.p(
                f"${row['market_value']:,.2f}",
                class_name="font-mono text-xs tabular-nums font-semibold text-[#10231F]",
            ),
            rx.el.p(
                f"${row['gain']:,.2f}",
                class_name=rx.cond(
                    row["gain"] >= 0,
                    "font-mono text-[11px] tabular-nums text-emerald-700",
                    "font-mono text-[11px] tabular-nums text-red-700",
                ),
            ),
            class_name="px-3 py-2.5 text-right align-top",
        ),
        rx.el.td(_role_actions(row), class_name="px-3 py-2.5 align-top"),
        class_name="border-b border-[#10231F]/10 odd:bg-[#FFFDF8] even:bg-[#F7F2E7] transition-colors hover:bg-emerald-500/5",
    )


def _user_card(row: AdminUserRow) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    row["display_name"],
                    class_name="text-sm font-semibold text-[#10231F]",
                ),
                rx.el.p(
                    row["email"],
                    class_name="font-mono text-xs text-[#10231F]/60",
                ),
                class_name="flex flex-col",
            ),
            _role_badge(row),
            class_name="flex items-start justify-between gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.p(
                    "Holdings",
                    class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
                ),
                rx.el.p(
                    row["holding_count"].to_string(),
                    class_name="font-mono text-xs tabular-nums text-[#10231F]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.p(
                    "Market value",
                    class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
                ),
                rx.el.p(
                    f"${row['market_value']:,.2f}",
                    class_name="font-mono text-xs tabular-nums text-[#10231F]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.p(
                    "Cost basis",
                    class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
                ),
                rx.el.p(
                    f"${row['cost_basis']:,.2f}",
                    class_name="font-mono text-xs tabular-nums text-[#10231F]",
                ),
                class_name="flex flex-col",
            ),
            rx.el.div(
                rx.el.p(
                    "Registered",
                    class_name="font-mono text-[10px] uppercase tracking-[0.14em] text-[#10231F]/50",
                ),
                rx.el.p(
                    row["created_at"],
                    class_name="font-mono text-xs tabular-nums text-[#10231F]",
                ),
                class_name="flex flex-col",
            ),
            class_name="mt-3 grid grid-cols-2 gap-2 border-t border-[#10231F]/10 pt-3",
        ),
        rx.el.div(
            _role_actions(row),
            class_name="mt-3 border-t border-[#10231F]/10 pt-3",
        ),
        class_name="w-full border border-[#10231F]/15 bg-[#FFFDF8] p-4",
    )


def _no_user_matches() -> rx.Component:
    return rx.el.div(
        rx.icon("user-x", class_name="h-5 w-5 text-[#10231F]/50"),
        rx.el.p(
            "No accounts match your search or filters.",
            class_name="mt-2 text-sm text-[#10231F]/65",
        ),
        rx.el.button(
            "Clear filters",
            type="button",
            on_click=AdminState.clear_user_filters,
            class_name="mt-3 border border-[#10231F]/25 px-3 py-1.5 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
        ),
        class_name="mt-4 flex w-full flex-col items-center justify-center border border-dashed border-[#10231F]/25 bg-[#FFFDF8] px-6 py-10 text-center",
    )


def _users_views() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.table(
                rx.el.thead(
                    rx.el.tr(
                        _th("user", "Account"),
                        _th("shield", "Role"),
                        _th("circle-dot", "Status"),
                        _th("calendar", "Registered"),
                        _th("hash", "Holdings", "justify-end"),
                        _th("receipt", "Cost basis", "justify-end"),
                        _th("wallet", "Market value", "justify-end"),
                        _th("settings-2", "Role change", "justify-end"),
                    )
                ),
                rx.el.tbody(rx.foreach(AdminState.filtered_users, _user_row)),
                class_name="w-full table-auto border-collapse",
            ),
            class_name="mt-4 hidden w-full overflow-hidden overflow-x-auto border border-[#10231F]/15 lg:block",
        ),
        rx.el.div(
            rx.foreach(AdminState.filtered_users, _user_card),
            class_name="mt-4 grid w-full grid-cols-1 gap-3 md:grid-cols-2 lg:hidden",
        ),
        class_name="w-full",
    )


def admin_users_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Accounts & roles",
                    class_name="font-serif text-lg text-[#10231F]",
                ),
                rx.el.p(
                    f"{AdminState.filtered_user_count} of {AdminState.total_users} accounts shown · passwords and session tokens are never displayed",
                    class_name="mt-1 font-mono text-[11px] text-[#10231F]/55",
                ),
                class_name="flex flex-col",
            ),
            rx.cond(
                AdminState.user_filters_active,
                rx.el.button(
                    "Clear filters",
                    type="button",
                    on_click=AdminState.clear_user_filters,
                    class_name="w-fit border border-[#10231F]/25 px-3 py-1.5 text-xs font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-col items-start justify-between gap-3 pb-4 sm:flex-row sm:items-center",
        ),
        rx.cond(
            AdminState.role_error != "",
            rx.el.div(
                rx.el.p(
                    AdminState.role_error,
                    role="alert",
                    class_name="text-sm text-amber-800",
                ),
                rx.el.button(
                    rx.icon("x", class_name="h-3.5 w-3.5"),
                    type="button",
                    aria_label="Dismiss",
                    on_click=AdminState.dismiss_role_error,
                    class_name="ml-auto text-amber-800",
                ),
                class_name="mb-4 flex items-center gap-3 border border-amber-600/40 bg-amber-500/10 px-3 py-2",
            ),
            rx.fragment(),
        ),
        _users_toolbar(),
        rx.cond(
            AdminState.has_users,
            rx.cond(
                AdminState.filtered_user_count > 0,
                _users_views(),
                _no_user_matches(),
            ),
            rx.el.p(
                "No accounts have registered yet.",
                class_name="mt-6 text-sm text-[#10231F]/55",
            ),
        ),
        class_name="mt-5 w-full border border-[#10231F]/15 bg-[#F5F0E6] p-5",
    )


def role_change_modal() -> rx.Component:
    return rx.cond(
        AdminState.role_target_id > 0,
        rx.el.div(
            rx.el.div(
                on_click=AdminState.cancel_role_change,
                class_name="absolute inset-0 bg-[#10231F]/55",
            ),
            rx.el.div(
                rx.el.h2(
                    rx.cond(
                        AdminState.role_target_new_role == "admin",
                        "Grant administrator access?",
                        "Remove administrator access?",
                    ),
                    class_name="font-serif text-xl text-[#10231F]",
                ),
                rx.el.p(
                    AdminState.role_target_label,
                    class_name="mt-2 font-mono text-sm text-[#10231F]/70",
                ),
                rx.el.p(
                    rx.cond(
                        AdminState.role_target_new_role == "admin",
                        "This account will be able to inspect every portfolio and change roles.",
                        "This account will keep its own portfolio but lose all oversight access.",
                    ),
                    class_name="mt-3 text-sm text-[#10231F]/60",
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        type="button",
                        on_click=AdminState.cancel_role_change,
                        class_name="border border-[#10231F]/25 px-4 py-2 text-sm font-medium text-[#10231F] transition-colors hover:bg-[#10231F]/5",
                    ),
                    rx.el.button(
                        rx.cond(
                            AdminState.is_changing_role,
                            "Applying…",
                            "Confirm change",
                        ),
                        type="button",
                        disabled=AdminState.is_changing_role,
                        on_click=AdminState.confirm_role_change,
                        class_name="bg-[#10231F] px-4 py-2 text-sm font-semibold text-[#F5F0E6] transition-colors hover:bg-emerald-800 disabled:opacity-60",
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

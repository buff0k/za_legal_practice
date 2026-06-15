# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe


def has_app_permission() -> bool:
    """
    Check if the user has permission to access this app.

    This function is intended to be called from hooks.py, for example:

        has_permission = "your_app.has_app_permission.has_app_permission"

    For now, access is intentionally open to all logged-in users.
    Role-based restrictions can be added later when required.
    """

    # Allow Administrator
    if frappe.session.user == "Administrator":
        return True

    # Allow all logged-in users for now.
    # Future tightening can check frappe.get_roles(frappe.session.user)
    # against a required_roles list.
    if frappe.session.user and frappe.session.user != "Guest":
        return True

    # Do not show the app to Guest / unauthenticated users.
    return False
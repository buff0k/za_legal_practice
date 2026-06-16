# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime


class AttorneyProfile(Document):
    """Attorney master record for the ZA Legal Practice app.

    Design notes:
    - This DocType links to Frappe User by default.
    - HRMS / Employee is optional and must not be required.
    - Trust Account means ERPNext Bank Account.
    - Trust Bank GL Account means the Account linked to the Bank Account.
    """

    def validate(self):
        self.set_runtime_flags()
        self.set_user_details()
        self.validate_user()
        self.validate_hrms_fields()
        self.validate_professional_flags()
        self.validate_supervision()
        self.validate_company_scoped_links()
        self.validate_trust_access()
        self.validate_billing_defaults()

    def on_update(self):
        if cint(self.auto_create_user_permissions):
            self.sync_user_permissions()

    @frappe.whitelist()
    def refresh_runtime_flags(self):
        self.set_runtime_flags()
        return {
            "hrms_installed": cint(self.hrms_installed),
        }

    @frappe.whitelist()
    def sync_user_permissions(self):
        """Create/update basic User Permission records for the attorney.

        This intentionally only creates permissions for:
        - Bank Account records listed in permitted_trust_accounts
        - Branch, if set
        - Cost Center, if set

        Matter/client permissions should be created by Matter workflows or assignment logic,
        not globally from the Attorney Profile.
        """

        if not self.user:
            frappe.throw(_("User is required before syncing permissions."))

        if cint(self.disabled) or self.status != "Active":
            return {"synced": 0, "reason": "Attorney Profile is disabled or inactive."}

        created = 0

        if cint(self.enforce_trust_account_restrictions):
            for row in self.get("permitted_trust_accounts") or []:
                if cint(row.disabled):
                    continue

                if row.trust_account:
                    created += create_user_permission(
                        user=self.user,
                        allow="Bank Account",
                        for_value=row.trust_account,
                    )

        if self.branch:
            created += create_user_permission(
                user=self.user,
                allow="Branch",
                for_value=self.branch,
            )

        if self.cost_center:
            created += create_user_permission(
                user=self.user,
                allow="Cost Center",
                for_value=self.cost_center,
            )

        self.db_set("last_user_permission_sync", now_datetime(), update_modified=False)

        return {
            "synced": 1,
            "created": created,
        }

    def set_runtime_flags(self):
        self.hrms_installed = 1 if is_hrms_installed() else 0

    def set_user_details(self):
        if not self.user:
            return

        user_details = frappe.db.get_value(
            "User",
            self.user,
            ["full_name", "email", "enabled", "mobile_no", "phone"],
            as_dict=True,
        )

        if not user_details:
            return

        if not self.attorney_name:
            self.attorney_name = user_details.full_name or self.user

        self.email = user_details.email or self.user

        if not self.mobile_no and user_details.mobile_no:
            self.mobile_no = user_details.mobile_no

        if not self.phone and user_details.phone:
            self.phone = user_details.phone

    def validate_user(self):
        if not self.user:
            frappe.throw(_("User is required."))

        user_details = frappe.db.get_value(
            "User",
            self.user,
            ["enabled", "user_type"],
            as_dict=True,
        )

        if not user_details:
            frappe.throw(_("User {0} does not exist.").format(frappe.bold(self.user)))

        if not cint(user_details.enabled):
            frappe.throw(_("User {0} is disabled.").format(frappe.bold(self.user)))

        duplicate = frappe.db.exists(
            "Attorney Profile",
            {
                "user": self.user,
                "name": ["!=", self.name],
            },
        )
        if duplicate:
            frappe.throw(
                _("User {0} is already linked to Attorney Profile {1}.").format(
                    frappe.bold(self.user),
                    frappe.bold(duplicate),
                )
            )

    def validate_hrms_fields(self):
        if self.employee and not cint(self.hrms_installed):
            frappe.throw(
                _("Employee is set, but HRMS/Frappe HR is not installed. Clear Employee or install HRMS.")
            )

        if cint(self.enable_optional_employee_link) and not cint(self.hrms_installed):
            frappe.throw(
                _("Optional Employee Link cannot be enabled because HRMS/Frappe HR is not installed.")
            )

        if self.employee and frappe.db.exists("Employee", self.employee):
            employee_user = frappe.db.get_value("Employee", self.employee, "user_id")
            if employee_user and employee_user != self.user:
                frappe.throw(
                    _("Employee {0} is linked to User {1}, but this Attorney Profile is linked to User {2}.").format(
                        frappe.bold(self.employee),
                        frappe.bold(employee_user),
                        frappe.bold(self.user),
                    )
                )

    def validate_professional_flags(self):
        if self.attorney_type == "Candidate Attorney":
            self.is_candidate_attorney = 1
            if cint(self.is_admitted_attorney):
                frappe.throw(_("Candidate Attorney cannot also be marked as an admitted attorney."))

        if self.attorney_type in {"Attorney", "Partner", "Director", "Consultant"}:
            if not cint(self.is_admitted_attorney) and self.status == "Active":
                frappe.throw(
                    _("Active {0} profiles should be marked as admitted attorneys.").format(self.attorney_type)
                )

        if self.right_of_appearance and self.right_of_appearance != "None" and not self.right_of_appearance_date:
            frappe.throw(_("Right of Appearance Date is required when Right of Appearance is set."))

    def validate_supervision(self):
        if cint(self.requires_supervision) and not self.supervising_attorney:
            frappe.throw(_("Supervising Attorney is required when Requires Supervision is enabled."))

        if self.supervising_attorney == self.name:
            frappe.throw(_("An Attorney Profile cannot supervise itself."))

        if self.supervising_attorney:
            supervisor_status = frappe.db.get_value("Attorney Profile", self.supervising_attorney, "status")
            if supervisor_status and supervisor_status != "Active":
                frappe.throw(_("Supervising Attorney must be active."))

    def validate_company_scoped_links(self):
        default_company = get_default_company_from_settings()
        if not default_company:
            return

        if self.cost_center:
            company = frappe.db.get_value("Cost Center", self.cost_center, "company")
            if company and company != default_company:
                frappe.throw(
                    _("Cost Center must belong to Default Company {0}. Current company: {1}").format(
                        frappe.bold(default_company),
                        frappe.bold(company),
                    )
                )

    def validate_trust_access(self):
        if not cint(self.enforce_trust_account_restrictions):
            return

        seen = set()
        default_count = 0
        active_rows = []

        for row in self.get("permitted_trust_accounts") or []:
            if cint(row.disabled):
                continue

            if not row.trust_account:
                continue

            if row.trust_account in seen:
                frappe.throw(_("Trust Account {0} is listed more than once.").format(frappe.bold(row.trust_account)))

            seen.add(row.trust_account)
            active_rows.append(row)

            gl_account = get_bank_account_gl_account(row.trust_account)
            if gl_account and row.trust_bank_gl_account != gl_account:
                row.trust_bank_gl_account = gl_account

            validate_bank_account(row.trust_account, "Trust Account")

            if cint(row.is_default):
                default_count += 1

        if default_count > 1:
            frappe.throw(_("Only one permitted Trust Account may be marked as default."))

        if self.default_trust_account:
            validate_bank_account(self.default_trust_account, "Default Trust Account")

            if self.default_trust_account not in seen:
                frappe.throw(
                    _("Default Trust Account must also be listed under Permitted Trust Accounts.")
                )

            default_gl = get_bank_account_gl_account(self.default_trust_account)
            if default_gl:
                self.default_trust_bank_gl_account = default_gl

        if not self.default_trust_account and active_rows:
            default_rows = [row for row in active_rows if cint(row.is_default)]
            selected = default_rows[0] if default_rows else active_rows[0]
            self.default_trust_account = selected.trust_account
            self.default_trust_bank_gl_account = selected.trust_bank_gl_account or get_bank_account_gl_account(
                selected.trust_account
            )

    def validate_billing_defaults(self):
        if flt(self.default_hourly_rate) < 0:
            frappe.throw(_("Default Hourly Rate cannot be negative."))

        for fieldname, label in {
            "default_hourly_rate_item": _("Default Hourly Rate Item"),
            "default_consultation_item": _("Default Consultation Item"),
        }.items():
            item = self.get(fieldname)
            if not item:
                continue

            if not frappe.db.exists("Item", item):
                frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(item)))

            disabled = frappe.db.get_value("Item", item, "disabled")
            if cint(disabled):
                frappe.throw(_("{0} {1} is disabled.").format(label, frappe.bold(item)))


def is_hrms_installed():
    installed_apps = set(frappe.get_installed_apps())
    if "hrms" in installed_apps:
        return True

    return bool(frappe.db.exists("Module Def", "HR"))


def get_default_company_from_settings():
    if frappe.db.exists("DocType", "Legal Practice Settings"):
        default_company = frappe.db.get_single_value("Legal Practice Settings", "default_company")
        if default_company:
            return default_company

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.defaults.get_global_default("company")
        or frappe.defaults.get_global_default("Company")
    )

    if company and frappe.db.exists("Company", company):
        return company

    companies = frappe.get_all("Company", pluck="name", limit=2)
    if len(companies) == 1:
        return companies[0]

    return None


def get_bank_account_gl_account(bank_account):
    if not bank_account or not frappe.db.exists("Bank Account", bank_account):
        return None

    meta = frappe.get_meta("Bank Account")
    for fieldname in ("account", "gl_account"):
        if meta.has_field(fieldname):
            return frappe.db.get_value("Bank Account", bank_account, fieldname)

    return None


def get_bank_account_company(bank_account):
    if not bank_account or not frappe.db.exists("Bank Account", bank_account):
        return None

    meta = frappe.get_meta("Bank Account")

    if meta.has_field("company"):
        company = frappe.db.get_value("Bank Account", bank_account, "company")
        if company:
            return company

    gl_account = get_bank_account_gl_account(bank_account)
    if gl_account:
        return frappe.db.get_value("Account", gl_account, "company")

    return None


def validate_bank_account(bank_account, label):
    if not frappe.db.exists("Bank Account", bank_account):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(bank_account)))

    default_company = get_default_company_from_settings()
    bank_company = get_bank_account_company(bank_account)

    if default_company and bank_company and bank_company != default_company:
        frappe.throw(
            _("{0} must belong to Default Company {1}. Current company: {2}").format(
                label,
                frappe.bold(default_company),
                frappe.bold(bank_company),
            )
        )

    gl_account = get_bank_account_gl_account(bank_account)
    if gl_account:
        details = frappe.db.get_value(
            "Account",
            gl_account,
            ["account_type", "root_type", "is_group", "disabled"],
            as_dict=True,
        )

        if details:
            if cint(details.is_group):
                frappe.throw(_("{0}'s linked GL Account must not be a group account.").format(label))

            if cint(details.disabled):
                frappe.throw(_("{0}'s linked GL Account is disabled.").format(label))

            if details.account_type != "Bank":
                frappe.throw(
                    _("{0}'s linked GL Account must have Account Type Bank. Current type: {1}").format(
                        label,
                        details.account_type or "Not Set",
                    )
                )


def create_user_permission(user, allow, for_value):
    if not user or not allow or not for_value:
        return 0

    exists = frappe.db.exists(
        "User Permission",
        {
            "user": user,
            "allow": allow,
            "for_value": for_value,
        },
    )

    if exists:
        return 0

    doc = frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": allow,
            "for_value": for_value,
            "apply_to_all_doctypes": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return 1
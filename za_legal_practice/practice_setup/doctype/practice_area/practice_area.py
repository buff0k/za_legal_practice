# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class PracticeArea(Document):
    """Practice Area master for ZA Legal Practice.

    Practice Area is a setup/master DocType, not a transaction DocType.

    It provides defaults for:
    - Matter opening
    - Responsible attorney
    - Cost center / branch
    - Trust account defaults
    - Billing account defaults
    - Compliance behaviour
    """

    def validate(self):
        self.set_defaults_from_legal_practice_settings()
        self.normalize_area_code()
        self.set_trust_bank_gl_account()
        self.validate_parent()
        self.validate_area_code()
        self.validate_responsible_attorney()
        self.validate_company_scoped_links()
        self.validate_trust_defaults()
        self.validate_billing_defaults()
        self.validate_matter_defaults()
        self.validate_status()

    def set_defaults_from_legal_practice_settings(self):
        settings = get_legal_practice_settings()

        if not settings:
            return

        if not self.default_branch and settings.get("default_branch"):
            self.default_branch = settings.default_branch

        if not self.default_cost_center and settings.get("default_cost_center"):
            self.default_cost_center = settings.default_cost_center

        if not self.default_trust_account and settings.get("default_trust_account"):
            self.default_trust_account = settings.default_trust_account

        if not self.default_trust_creditor_account and settings.get("default_trust_creditor_account"):
            self.default_trust_creditor_account = settings.default_trust_creditor_account

        if not self.default_income_account and settings.get("default_professional_fees_income_account"):
            self.default_income_account = settings.default_professional_fees_income_account

        if not self.default_disbursement_recovery_account and settings.get("default_disbursement_recovery_account"):
            self.default_disbursement_recovery_account = settings.default_disbursement_recovery_account

        if not self.default_sales_taxes_and_charges_template and settings.get("default_sales_taxes_and_charges_template"):
            self.default_sales_taxes_and_charges_template = settings.default_sales_taxes_and_charges_template

        if not self.default_hourly_rate_item and settings.get("default_hourly_rate_item"):
            self.default_hourly_rate_item = settings.default_hourly_rate_item

        if not self.default_consultation_item and settings.get("default_consultation_item"):
            self.default_consultation_item = settings.default_consultation_item

        if not self.default_disbursement_item and settings.get("default_disbursement_item"):
            self.default_disbursement_item = settings.default_disbursement_item

    def normalize_area_code(self):
        if not self.area_code and self.practice_area_name:
            self.area_code = make_code(self.practice_area_name)

        if self.area_code:
            self.area_code = make_code(self.area_code)

        if not self.matter_number_prefix and self.area_code:
            self.matter_number_prefix = self.area_code

        if self.matter_number_prefix:
            self.matter_number_prefix = make_code(self.matter_number_prefix)

    def set_trust_bank_gl_account(self):
        if not self.default_trust_account:
            self.default_trust_bank_gl_account = None
            return

        linked_account = get_bank_account_gl_account(self.default_trust_account)

        if linked_account:
            self.default_trust_bank_gl_account = linked_account

    def validate_parent(self):
        if self.parent_practice_area and self.parent_practice_area == self.name:
            frappe.throw(_("Practice Area cannot be its own parent."))

        if self.parent_practice_area:
            parent = frappe.db.get_value(
                "Practice Area",
                self.parent_practice_area,
                ["disabled", "status"],
                as_dict=True,
            )

            if not parent:
                frappe.throw(_("Parent Practice Area {0} does not exist.").format(frappe.bold(self.parent_practice_area)))

            if cint(parent.disabled):
                frappe.throw(_("Parent Practice Area is disabled."))

            if parent.status != "Active":
                frappe.throw(_("Parent Practice Area must be Active."))

    def validate_area_code(self):
        if not self.area_code:
            frappe.throw(_("Area Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.area_code):
            frappe.throw(_("Area Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Practice Area",
            {
                "area_code": self.area_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Area Code {0} is already used by Practice Area {1}.").format(
                    frappe.bold(self.area_code),
                    frappe.bold(duplicate),
                )
            )

    def validate_responsible_attorney(self):
        if not self.responsible_attorney:
            return

        attorney = frappe.db.get_value(
            "Attorney Profile",
            self.responsible_attorney,
            ["status", "disabled"],
            as_dict=True,
        )

        if not attorney:
            frappe.throw(_("Responsible Attorney {0} does not exist.").format(frappe.bold(self.responsible_attorney)))

        if attorney.status != "Active" or cint(attorney.disabled):
            frappe.throw(_("Responsible Attorney must be active."))

    def validate_company_scoped_links(self):
        company = get_default_company()

        if not company:
            return

        if self.default_cost_center:
            cost_center_company = frappe.db.get_value("Cost Center", self.default_cost_center, "company")
            if cost_center_company and cost_center_company != company:
                frappe.throw(
                    _("Default Cost Center must belong to Default Company {0}. Current company: {1}").format(
                        frappe.bold(company),
                        frappe.bold(cost_center_company),
                    )
                )

        account_fields = {
            "default_trust_bank_gl_account": _("Default Trust Bank GL Account"),
            "default_trust_creditor_account": _("Default Trust Creditor Account"),
            "default_income_account": _("Default Income Account"),
            "default_disbursement_recovery_account": _("Default Disbursement Recovery Account"),
        }

        for fieldname, label in account_fields.items():
            account = self.get(fieldname)
            if account:
                validate_account_company(account, company, label)

        if self.default_trust_account:
            bank_account_company = get_bank_account_company(self.default_trust_account)
            if bank_account_company and bank_account_company != company:
                frappe.throw(
                    _("Default Trust Account must belong to Default Company {0}. Current company: {1}").format(
                        frappe.bold(company),
                        frappe.bold(bank_account_company),
                    )
                )

        if self.default_sales_taxes_and_charges_template:
            validate_template_company(
                "Sales Taxes and Charges Template",
                self.default_sales_taxes_and_charges_template,
                company,
            )

    def validate_trust_defaults(self):
        settings = get_legal_practice_settings()
        trust_enabled = cint(settings.get("enable_trust_accounting")) if settings else True

        if not trust_enabled:
            return

        if cint(self.require_trust_account_on_matter) and not self.default_trust_account:
            # Do not hard-block group nodes. They often exist only for hierarchy.
            if not cint(self.is_group):
                frappe.throw(_("Default Trust Account is required when this Practice Area requires trust accounts on matters."))

        if self.default_trust_account:
            validate_bank_account(self.default_trust_account, _("Default Trust Account"))

        if self.default_trust_bank_gl_account:
            validate_bank_gl_account(self.default_trust_bank_gl_account, _("Default Trust Bank GL Account"))

        if self.default_trust_creditor_account:
            validate_trust_creditor_account(self.default_trust_creditor_account)

    def validate_billing_defaults(self):
        for fieldname, label in {
            "default_hourly_rate_item": _("Default Hourly Rate Item"),
            "default_consultation_item": _("Default Consultation Item"),
            "default_disbursement_item": _("Default Disbursement Item"),
        }.items():
            item = self.get(fieldname)
            if item:
                validate_item(item, label)

    def validate_matter_defaults(self):
        if self.default_matter_workflow:
            workflow = frappe.db.get_value(
                "Workflow",
                self.default_matter_workflow,
                ["document_type", "is_active"],
                as_dict=True,
            )

            if not workflow:
                frappe.throw(_("Default Matter Workflow {0} does not exist.").format(frappe.bold(self.default_matter_workflow)))

            if workflow.document_type != "Matter":
                frappe.throw(_("Default Matter Workflow must be for the Matter DocType."))

            if not cint(workflow.is_active):
                frappe.throw(_("Default Matter Workflow must be active."))

    def validate_status(self):
        if cint(self.disabled) and self.status == "Active":
            self.status = "Inactive"

        if self.status != "Active" and not cint(self.disabled):
            # This keeps the disabled flag explicit but does not force it for Archived.
            if self.status == "Archived":
                self.disabled = 1


def make_code(value):
    value = (value or "").strip().upper()
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def get_legal_practice_settings():
    if not frappe.db.exists("DocType", "Legal Practice Settings"):
        return None

    try:
        return frappe.get_single("Legal Practice Settings")
    except Exception:
        return None


def get_default_company():
    settings = get_legal_practice_settings()

    if settings and settings.get("default_company"):
        return settings.default_company

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

    gl_account = get_bank_account_gl_account(bank_account)

    if gl_account:
        validate_bank_gl_account(gl_account, _("{0}'s linked GL Account").format(label))


def validate_account_company(account, company, label):
    if not frappe.db.exists("Account", account):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(account)))

    details = frappe.db.get_value(
        "Account",
        account,
        ["company", "is_group", "disabled"],
        as_dict=True,
    )

    if details.company != company:
        frappe.throw(
            _("{0} must belong to Default Company {1}. Current company: {2}").format(
                label,
                frappe.bold(company),
                frappe.bold(details.company),
            )
        )

    if cint(details.is_group):
        frappe.throw(_("{0} must not be a group account.").format(label))

    if cint(details.disabled):
        frappe.throw(_("{0} must not be disabled.").format(label))


def validate_bank_gl_account(account, label):
    if not frappe.db.exists("Account", account):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(account)))

    details = frappe.db.get_value(
        "Account",
        account,
        ["account_type", "root_type", "is_group", "disabled"],
        as_dict=True,
    )

    if cint(details.is_group):
        frappe.throw(_("{0} must not be a group account.").format(label))

    if cint(details.disabled):
        frappe.throw(_("{0} must not be disabled.").format(label))

    if details.account_type != "Bank":
        frappe.throw(
            _("{0} must have Account Type Bank. Current type: {1}").format(
                label,
                details.account_type or "Not Set",
            )
        )

    if details.root_type != "Asset":
        frappe.throw(
            _("{0} must be an Asset account. Current root type: {1}").format(
                label,
                details.root_type or "Not Set",
            )
        )


def validate_trust_creditor_account(account):
    if not frappe.db.exists("Account", account):
        frappe.throw(_("Default Trust Creditor Account {0} does not exist.").format(frappe.bold(account)))

    details = frappe.db.get_value(
        "Account",
        account,
        ["account_type", "root_type", "is_group", "disabled"],
        as_dict=True,
    )

    if cint(details.is_group):
        frappe.throw(_("Default Trust Creditor Account must not be a group account."))

    if cint(details.disabled):
        frappe.throw(_("Default Trust Creditor Account must not be disabled."))

    if details.account_type in {"Bank", "Cash"}:
        frappe.throw(_("Default Trust Creditor Account must not be a Bank or Cash account."))

    if details.root_type != "Liability":
        frappe.throw(
            _("Default Trust Creditor Account should be a Liability account. Current root type: {0}").format(
                details.root_type or "Not Set"
            )
        )


def validate_item(item, label):
    if not frappe.db.exists("Item", item):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(item)))

    disabled = frappe.db.get_value("Item", item, "disabled")

    if cint(disabled):
        frappe.throw(_("{0} {1} is disabled.").format(label, frappe.bold(item)))


def validate_template_company(doctype, name, company):
    if not frappe.db.exists(doctype, name):
        frappe.throw(_("{0} {1} does not exist.").format(doctype, frappe.bold(name)))

    meta = frappe.get_meta(doctype)

    if not meta.has_field("company"):
        return

    template_company = frappe.db.get_value(doctype, name, "company")

    if template_company and template_company != company:
        frappe.throw(
            _("{0} must belong to Default Company {1}. Current company: {2}").format(
                name,
                frappe.bold(company),
                frappe.bold(template_company),
            )
        )
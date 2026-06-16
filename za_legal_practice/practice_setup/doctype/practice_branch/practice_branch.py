# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class PracticeBranch(Document):
    """Practice Branch master for ZA Legal Practice.

    Practice Branch is a legal-practice wrapper around ERPNext Branch.

    It provides branch-specific defaults for:
    - Matter opening
    - Responsible attorneys
    - Trust account defaults
    - Business accounting defaults
    - Billing defaults
    - Compliance defaults
    """

    def validate(self):
        self.set_defaults_from_legal_practice_settings()
        self.normalize_branch_code()
        self.set_bank_gl_accounts()
        self.validate_branch_code()
        self.validate_erpnext_branch()
        self.validate_attorney_links()
        self.validate_practice_area()
        self.validate_company_scoped_links()
        self.validate_trust_defaults()
        self.validate_business_defaults()
        self.validate_matter_defaults()
        self.validate_status()

    def set_defaults_from_legal_practice_settings(self):
        settings = get_legal_practice_settings()

        if not settings:
            return

        if not self.erpnext_branch and settings.get("default_branch"):
            self.erpnext_branch = settings.default_branch

        if not self.default_cost_center and settings.get("default_cost_center"):
            self.default_cost_center = settings.default_cost_center

        if not self.default_business_bank_account and settings.get("default_business_bank_account"):
            self.default_business_bank_account = settings.default_business_bank_account

        if not self.default_business_bank_gl_account and settings.get("default_business_bank_gl_account"):
            self.default_business_bank_gl_account = settings.default_business_bank_gl_account

        if not self.default_trust_account and settings.get("default_trust_account"):
            self.default_trust_account = settings.default_trust_account

        if not self.default_trust_bank_gl_account and settings.get("default_trust_bank_gl_account"):
            self.default_trust_bank_gl_account = settings.default_trust_bank_gl_account

        if not self.default_trust_creditor_account and settings.get("default_trust_creditor_account"):
            self.default_trust_creditor_account = settings.default_trust_creditor_account

        if not self.default_income_account and settings.get("default_professional_fees_income_account"):
            self.default_income_account = settings.default_professional_fees_income_account

        if not self.default_receivable_account and settings.get("default_receivable_account"):
            self.default_receivable_account = settings.default_receivable_account

        if not self.default_disbursement_recovery_account and settings.get("default_disbursement_recovery_account"):
            self.default_disbursement_recovery_account = settings.default_disbursement_recovery_account

        if not self.default_write_off_account and settings.get("default_write_off_account"):
            self.default_write_off_account = settings.default_write_off_account

        if not self.default_sales_taxes_and_charges_template and settings.get("default_sales_taxes_and_charges_template"):
            self.default_sales_taxes_and_charges_template = settings.default_sales_taxes_and_charges_template

        if not self.trust_reconciliation_reviewer_role and settings.get("trust_reconciliation_reviewer_role"):
            self.trust_reconciliation_reviewer_role = settings.trust_reconciliation_reviewer_role

        if not self.matter_closing_approval_role and settings.get("matter_closing_approval_role"):
            self.matter_closing_approval_role = settings.matter_closing_approval_role

        if not self.invoice_approval_role and settings.get("invoice_approval_role"):
            self.invoice_approval_role = settings.invoice_approval_role

    def normalize_branch_code(self):
        if not self.branch_code and self.branch_name:
            self.branch_code = make_code(self.branch_name)

        if self.branch_code:
            self.branch_code = make_code(self.branch_code)

        if not self.matter_number_prefix and self.branch_code:
            self.matter_number_prefix = self.branch_code

        if self.matter_number_prefix:
            self.matter_number_prefix = make_code(self.matter_number_prefix)

    def set_bank_gl_accounts(self):
        if self.default_business_bank_account:
            business_gl = get_bank_account_gl_account(self.default_business_bank_account)
            if business_gl:
                self.default_business_bank_gl_account = business_gl

        if self.default_trust_account:
            trust_gl = get_bank_account_gl_account(self.default_trust_account)
            if trust_gl:
                self.default_trust_bank_gl_account = trust_gl

    def validate_branch_code(self):
        if not self.branch_code:
            frappe.throw(_("Branch Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.branch_code):
            frappe.throw(_("Branch Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Practice Branch",
            {
                "branch_code": self.branch_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Branch Code {0} is already used by Practice Branch {1}.").format(
                    frappe.bold(self.branch_code),
                    frappe.bold(duplicate),
                )
            )

    def validate_erpnext_branch(self):
        if not self.erpnext_branch:
            return

        if not frappe.db.exists("Branch", self.erpnext_branch):
            frappe.throw(_("ERPNext Branch {0} does not exist.").format(frappe.bold(self.erpnext_branch)))

        duplicate = frappe.db.exists(
            "Practice Branch",
            {
                "erpnext_branch": self.erpnext_branch,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("ERPNext Branch {0} is already linked to Practice Branch {1}.").format(
                    frappe.bold(self.erpnext_branch),
                    frappe.bold(duplicate),
                )
            )

    def validate_attorney_links(self):
        for fieldname, label in {
            "branch_manager": _("Branch Manager"),
            "responsible_partner": _("Responsible Partner"),
            "default_attorney": _("Default Attorney"),
        }.items():
            attorney = self.get(fieldname)

            if not attorney:
                continue

            validate_active_attorney(attorney, label)

        if self.responsible_partner:
            attorney_type = frappe.db.get_value("Attorney Profile", self.responsible_partner, "attorney_type")
            if attorney_type not in {"Partner", "Director"}:
                frappe.throw(_("Responsible Partner must be an Attorney Profile of type Partner or Director."))

    def validate_practice_area(self):
        if not self.default_practice_area:
            return

        area = frappe.db.get_value(
            "Practice Area",
            self.default_practice_area,
            ["status", "disabled", "is_group"],
            as_dict=True,
        )

        if not area:
            frappe.throw(_("Default Practice Area {0} does not exist.").format(frappe.bold(self.default_practice_area)))

        if area.status != "Active" or cint(area.disabled):
            frappe.throw(_("Default Practice Area must be active."))

        if cint(area.is_group):
            frappe.throw(_("Default Practice Area must be a leaf Practice Area, not a group."))

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

        if self.default_warehouse:
            warehouse_company = frappe.db.get_value("Warehouse", self.default_warehouse, "company")
            if warehouse_company and warehouse_company != company:
                frappe.throw(
                    _("Default Warehouse must belong to Default Company {0}. Current company: {1}").format(
                        frappe.bold(company),
                        frappe.bold(warehouse_company),
                    )
                )

        account_fields = {
            "default_business_bank_gl_account": _("Default Business Bank GL Account"),
            "default_trust_bank_gl_account": _("Default Trust Bank GL Account"),
            "default_trust_creditor_account": _("Default Trust Creditor Account"),
            "default_income_account": _("Default Income Account"),
            "default_receivable_account": _("Default Receivable Account"),
            "default_disbursement_recovery_account": _("Default Disbursement Recovery Account"),
            "default_write_off_account": _("Default Write-Off Account"),
        }

        for fieldname, label in account_fields.items():
            account = self.get(fieldname)
            if account:
                validate_account_company(account, company, label)

        for fieldname, label in {
            "default_business_bank_account": _("Default Business Bank Account"),
            "default_trust_account": _("Default Trust Account"),
        }.items():
            bank_account = self.get(fieldname)
            if bank_account:
                bank_company = get_bank_account_company(bank_account)
                if bank_company and bank_company != company:
                    frappe.throw(
                        _("{0} must belong to Default Company {1}. Current company: {2}").format(
                            label,
                            frappe.bold(company),
                            frappe.bold(bank_company),
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
            frappe.throw(_("Default Trust Account is required when this branch requires trust account on matters."))

        if self.default_trust_account:
            validate_bank_account(self.default_trust_account, _("Default Trust Account"))

        if self.default_trust_bank_gl_account:
            validate_bank_gl_account(self.default_trust_bank_gl_account, _("Default Trust Bank GL Account"))

        if self.default_trust_creditor_account:
            validate_trust_creditor_account(self.default_trust_creditor_account)

    def validate_business_defaults(self):
        if self.default_business_bank_account:
            validate_bank_account(self.default_business_bank_account, _("Default Business Bank Account"))

        if self.default_business_bank_gl_account:
            validate_bank_gl_account(self.default_business_bank_gl_account, _("Default Business Bank GL Account"))

        if self.default_income_account:
            validate_income_account(self.default_income_account, _("Default Income Account"))

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


def validate_active_attorney(attorney_profile, label):
    if not frappe.db.exists("Attorney Profile", attorney_profile):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(attorney_profile)))

    attorney = frappe.db.get_value(
        "Attorney Profile",
        attorney_profile,
        ["status", "disabled"],
        as_dict=True,
    )

    if attorney.status != "Active" or cint(attorney.disabled):
        frappe.throw(_("{0} must be active.").format(label))


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


def validate_income_account(account, label):
    if not frappe.db.exists("Account", account):
        frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(account)))

    details = frappe.db.get_value(
        "Account",
        account,
        ["root_type", "is_group", "disabled"],
        as_dict=True,
    )

    if cint(details.is_group):
        frappe.throw(_("{0} must not be a group account.").format(label))

    if cint(details.disabled):
        frappe.throw(_("{0} must not be disabled.").format(label))

    if details.root_type != "Income":
        frappe.throw(
            _("{0} should be an Income account. Current root type: {1}").format(
                label,
                details.root_type or "Not Set",
            )
        )


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
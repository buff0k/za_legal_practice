# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class MatterType(Document):
    """Matter Type master for ZA Legal Practice.

    Matter Type defines operational behaviour for matters:
    - workflow/default status
    - trust-account handling
    - compliance requirements
    - billing defaults
    - module-specific field enablement
    - default documents, checklist items, tasks, and billing items
    """

    def validate(self):
        self.set_defaults_from_related_setup()
        self.normalize_matter_type_code()
        self.set_trust_bank_gl_account()
        self.validate_matter_type_code()
        self.validate_practice_area()
        self.validate_practice_branch()
        self.validate_default_uniqueness()
        self.validate_company_scoped_links()
        self.validate_trust_settings()
        self.validate_billing_settings()
        self.validate_workflow_settings()
        self.validate_child_tables()
        self.validate_status()

    def set_defaults_from_related_setup(self):
        settings = get_legal_practice_settings()

        if settings:
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

            if not self.matter_closing_approval_role and settings.get("matter_closing_approval_role"):
                self.matter_closing_approval_role = settings.matter_closing_approval_role

        if self.practice_area and frappe.db.exists("Practice Area", self.practice_area):
            area = frappe.db.get_value(
                "Practice Area",
                self.practice_area,
                [
                    "matter_number_prefix",
                    "default_matter_status",
                    "default_matter_workflow",
                    "default_trust_account",
                    "default_trust_creditor_account",
                    "default_income_account",
                    "default_disbursement_recovery_account",
                    "default_sales_taxes_and_charges_template",
                    "require_conflict_check",
                    "require_fica",
                    "require_mandate",
                    "enable_litigation_fields",
                    "enable_conveyancing_fields",
                    "enable_collections_fields",
                    "enable_estates_fields",
                ],
                as_dict=True,
            )

            if area:
                if not self.matter_number_prefix and area.matter_number_prefix:
                    self.matter_number_prefix = area.matter_number_prefix

                if not self.default_matter_status and area.default_matter_status:
                    self.default_matter_status = area.default_matter_status

                if not self.default_matter_workflow and area.default_matter_workflow:
                    self.default_matter_workflow = area.default_matter_workflow

                if not self.default_trust_account and area.default_trust_account:
                    self.default_trust_account = area.default_trust_account

                if not self.default_trust_creditor_account and area.default_trust_creditor_account:
                    self.default_trust_creditor_account = area.default_trust_creditor_account

                if not self.default_income_account and area.default_income_account:
                    self.default_income_account = area.default_income_account

                if not self.default_disbursement_recovery_account and area.default_disbursement_recovery_account:
                    self.default_disbursement_recovery_account = area.default_disbursement_recovery_account

                if not self.default_sales_taxes_and_charges_template and area.default_sales_taxes_and_charges_template:
                    self.default_sales_taxes_and_charges_template = area.default_sales_taxes_and_charges_template

                self.require_conflict_check = cint(area.require_conflict_check)
                self.require_fica = cint(area.require_fica)
                self.require_mandate = cint(area.require_mandate)

                if cint(area.enable_litigation_fields):
                    self.enable_litigation_fields = 1
                if cint(area.enable_conveyancing_fields):
                    self.enable_conveyancing_fields = 1
                if cint(area.enable_collections_fields):
                    self.enable_collections_fields = 1
                if cint(area.enable_estates_fields):
                    self.enable_estates_fields = 1

        if self.practice_branch and frappe.db.exists("Practice Branch", self.practice_branch):
            branch = frappe.db.get_value(
                "Practice Branch",
                self.practice_branch,
                [
                    "matter_number_prefix",
                    "default_matter_status",
                    "default_matter_workflow",
                    "default_trust_account",
                    "default_trust_creditor_account",
                    "default_income_account",
                    "default_disbursement_recovery_account",
                    "default_sales_taxes_and_charges_template",
                    "require_conflict_check",
                    "require_fica",
                    "require_mandate",
                    "invoice_approval_role",
                    "matter_closing_approval_role",
                ],
                as_dict=True,
            )

            if branch:
                if not self.matter_number_prefix and branch.matter_number_prefix:
                    self.matter_number_prefix = branch.matter_number_prefix

                if not self.default_matter_status and branch.default_matter_status:
                    self.default_matter_status = branch.default_matter_status

                if not self.default_matter_workflow and branch.default_matter_workflow:
                    self.default_matter_workflow = branch.default_matter_workflow

                if not self.default_trust_account and branch.default_trust_account:
                    self.default_trust_account = branch.default_trust_account

                if not self.default_trust_creditor_account and branch.default_trust_creditor_account:
                    self.default_trust_creditor_account = branch.default_trust_creditor_account

                if not self.default_income_account and branch.default_income_account:
                    self.default_income_account = branch.default_income_account

                if not self.default_disbursement_recovery_account and branch.default_disbursement_recovery_account:
                    self.default_disbursement_recovery_account = branch.default_disbursement_recovery_account

                if not self.default_sales_taxes_and_charges_template and branch.default_sales_taxes_and_charges_template:
                    self.default_sales_taxes_and_charges_template = branch.default_sales_taxes_and_charges_template

                if not self.matter_closing_approval_role and branch.matter_closing_approval_role:
                    self.matter_closing_approval_role = branch.matter_closing_approval_role

    def normalize_matter_type_code(self):
        if not self.matter_type_code and self.matter_type_name:
            self.matter_type_code = make_code(self.matter_type_name)

        if self.matter_type_code:
            self.matter_type_code = make_code(self.matter_type_code)

        if not self.matter_number_prefix and self.matter_type_code:
            self.matter_number_prefix = self.matter_type_code

        if self.matter_number_prefix:
            self.matter_number_prefix = make_code(self.matter_number_prefix)

    def set_trust_bank_gl_account(self):
        if not self.default_trust_account:
            self.default_trust_bank_gl_account = None
            return

        linked_account = get_bank_account_gl_account(self.default_trust_account)

        if linked_account:
            self.default_trust_bank_gl_account = linked_account

    def validate_matter_type_code(self):
        if not self.matter_type_code:
            frappe.throw(_("Matter Type Code is required."))

        if not re.match(r"^[A-Z0-9_]+$", self.matter_type_code):
            frappe.throw(_("Matter Type Code may only contain uppercase letters, numbers, and underscores."))

        duplicate = frappe.db.exists(
            "Matter Type",
            {
                "matter_type_code": self.matter_type_code,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Matter Type Code {0} is already used by Matter Type {1}.").format(
                    frappe.bold(self.matter_type_code),
                    frappe.bold(duplicate),
                )
            )

    def validate_practice_area(self):
        if not self.practice_area:
            frappe.throw(_("Practice Area is required."))

        area = frappe.db.get_value(
            "Practice Area",
            self.practice_area,
            ["status", "disabled", "is_group"],
            as_dict=True,
        )

        if not area:
            frappe.throw(_("Practice Area {0} does not exist.").format(frappe.bold(self.practice_area)))

        if area.status != "Active" or cint(area.disabled):
            frappe.throw(_("Practice Area must be active."))

        if cint(area.is_group):
            frappe.throw(_("Practice Area must be a leaf Practice Area, not a group."))

    def validate_practice_branch(self):
        if not self.practice_branch:
            return

        branch = frappe.db.get_value(
            "Practice Branch",
            self.practice_branch,
            ["status", "disabled"],
            as_dict=True,
        )

        if not branch:
            frappe.throw(_("Practice Branch {0} does not exist.").format(frappe.bold(self.practice_branch)))

        if branch.status != "Active" or cint(branch.disabled):
            frappe.throw(_("Practice Branch must be active."))

    def validate_default_uniqueness(self):
        if not cint(self.is_default_for_practice_area):
            return

        filters = {
            "practice_area": self.practice_area,
            "is_default_for_practice_area": 1,
            "disabled": 0,
            "name": ["!=", self.name],
        }

        if self.practice_branch:
            filters["practice_branch"] = self.practice_branch
        else:
            filters["practice_branch"] = ["in", ["", None]]

        existing = frappe.db.exists("Matter Type", filters)

        if existing:
            frappe.throw(
                _("Matter Type {0} is already the default for this Practice Area/Branch combination.").format(
                    frappe.bold(existing)
                )
            )

    def validate_company_scoped_links(self):
        company = get_default_company()

        if not company:
            return

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

    def validate_trust_settings(self):
        if self.trust_handling == "Not Applicable":
            self.require_trust_account_on_matter = 0
            self.allow_trust_receipts = 0
            self.allow_trust_payments = 0
            self.allow_trust_to_business_transfers = 0
            return

        if self.trust_handling == "Required":
            self.require_trust_account_on_matter = 1

        if cint(self.require_trust_account_on_matter) and not self.default_trust_account:
            frappe.throw(_("Default Trust Account is required when this Matter Type requires trust account on matters."))

        if self.default_trust_account:
            validate_bank_account(self.default_trust_account, _("Default Trust Account"))

        if self.default_trust_bank_gl_account:
            validate_bank_gl_account(self.default_trust_bank_gl_account, _("Default Trust Bank GL Account"))

        if self.default_trust_creditor_account:
            validate_trust_creditor_account(self.default_trust_creditor_account)

    def validate_billing_settings(self):
        if self.billing_model != "No Charge" and not self.default_income_account:
            # Do not hard-block because ERPNext Item defaults may resolve income later.
            pass

        for fieldname, label in {
            "default_hourly_rate_item": _("Default Hourly Rate Item"),
            "default_consultation_item": _("Default Consultation Item"),
            "default_disbursement_item": _("Default Disbursement Item"),
        }.items():
            item = self.get(fieldname)
            if item:
                validate_item(item, label)

        for row in self.get("billing_items") or []:
            if cint(row.disabled):
                continue
            if row.item:
                validate_item(row.item, _("Billing Item"))
            if flt(row.default_qty) <= 0:
                frappe.throw(_("Default Qty must be greater than zero for billing item {0}.").format(row.item))

    def validate_workflow_settings(self):
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

    def validate_child_tables(self):
        self.validate_required_documents()
        self.validate_checklist_items()
        self.validate_default_tasks()

    def validate_required_documents(self):
        seen = set()

        for row in self.get("required_documents") or []:
            if cint(row.disabled):
                continue

            key = (row.document_name or "").strip().lower()

            if not key:
                frappe.throw(_("Required Document row {0}: Document Name is required.").format(row.idx))

            if key in seen:
                frappe.throw(_("Required Document {0} is duplicated.").format(frappe.bold(row.document_name)))

            seen.add(key)

    def validate_checklist_items(self):
        seen = set()

        for row in self.get("checklist_items") or []:
            if cint(row.disabled):
                continue

            key = (row.checklist_item or "").strip().lower()

            if not key:
                frappe.throw(_("Checklist row {0}: Checklist Item is required.").format(row.idx))

            if key in seen:
                frappe.throw(_("Checklist Item {0} is duplicated.").format(frappe.bold(row.checklist_item)))

            seen.add(key)

    def validate_default_tasks(self):
        seen = set()

        for row in self.get("default_tasks") or []:
            if cint(row.disabled):
                continue

            key = (row.task_subject or "").strip().lower()

            if not key:
                frappe.throw(_("Default Task row {0}: Task Subject is required.").format(row.idx))

            if key in seen:
                frappe.throw(_("Default Task {0} is duplicated.").format(frappe.bold(row.task_subject)))

            seen.add(key)

            if cint(row.due_days_from_matter_opening) < 0:
                frappe.throw(_("Due Days from Matter Opening cannot be negative for task {0}.").format(row.task_subject))

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
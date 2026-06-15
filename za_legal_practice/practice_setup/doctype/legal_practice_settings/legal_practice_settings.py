# Copyright (c) 2026, BuFf0k and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class LegalPracticeSettings(Document):
    """Global configuration for the ZA Legal Practice app.

    Important terminology:
    - default_trust_account is an ERPNext Bank Account record.
    - default_trust_bank_gl_account is the linked GL Account for that Bank Account.
    - default_trust_creditor_account is the trust liability/control Account.
    """

    def validate(self):
        self.set_runtime_flags()
        self.validate_core_required_fields()
        self.validate_hrms_strategy()
        self.validate_trust_accounting_settings()
        self.validate_bank_accounts()
        self.validate_gl_accounts()
        self.validate_tax_templates()
        self.validate_approval_consistency()
        self.validate_reconciliation_settings()
        self.validate_billing_and_time_settings()

    @frappe.whitelist()
    def refresh_runtime_flags(self):
        self.set_runtime_flags()
        return {
            "hrms_installed": cint(self.hrms_installed),
            "require_hrms": cint(self.require_hrms),
        }

    def set_runtime_flags(self):
        self.hrms_installed = 1 if is_hrms_installed() else 0
        # HRMS is not a hard dependency for this app. Keep this read-only switch off.
        self.require_hrms = 0

    def validate_core_required_fields(self):
        if not self.default_company:
            frappe.throw(_("Default Company is required."))

        if not self.practice_name:
            frappe.throw(_("Practice Name is required."))

        if not self.default_currency:
            frappe.throw(_("Default Currency is required."))

    def validate_hrms_strategy(self):
        if self.attorney_master_source == "Employee via HRMS" and not cint(self.hrms_installed):
            frappe.throw(
                _("HRMS/Frappe HR is not installed. Set Attorney Master Source to User or Attorney Profile.")
            )

        if (
            self.attorney_master_source != "Employee via HRMS"
            and cint(self.enable_optional_employee_link)
            and not cint(self.hrms_installed)
        ):
            frappe.throw(
                _("Optional Employee Link cannot be enabled because HRMS/Frappe HR is not installed.")
            )

    def validate_trust_accounting_settings(self):
        if not cint(self.enable_trust_accounting):
            return

        if not self.trust_account_model:
            frappe.throw(_("Trust Account Model is required when Trust Accounting is enabled."))

        if not self.default_trust_creditor_account:
            frappe.throw(_("Default Trust Creditor Account is required when Trust Accounting is enabled."))

        if self.trust_account_model == "Single Trust Account" and not self.default_trust_account:
            frappe.throw(_("Default Trust Account is required when Trust Account Model is Single Trust Account."))

        if cint(self.allow_multiple_trust_accounts_per_matter) and self.trust_account_model == "Single Trust Account":
            frappe.throw(
                _("Allow Multiple Trust Accounts per Matter cannot be enabled when the model is Single Trust Account.")
            )

        if cint(self.strict_validation_mode):
            required_switches = {
                "require_trust_account_on_matter": _("Require Trust Account on Matter"),
                "require_matter_dimension_on_trust_entries": _("Require Matter Dimension on Trust Entries"),
                "prevent_negative_matter_trust_balance": _("Prevent Negative Matter Trust Balance"),
                "prevent_negative_trust_account_balance": _("Prevent Negative Trust Account Balance"),
            }

            for fieldname, label in required_switches.items():
                if not cint(getattr(self, fieldname, 0)):
                    frappe.throw(
                        _("{0} must be enabled while Strict Validation Mode and Trust Accounting are enabled.").format(
                            label
                        )
                    )

    def validate_bank_accounts(self):
        bank_account_fields = {
            "default_business_bank_account": _("Default Business Bank Account"),
            "default_trust_account": _("Default Trust Account"),
        }

        for fieldname, label in bank_account_fields.items():
            bank_account = self.get(fieldname)
            if not bank_account:
                continue

            self.validate_bank_account_company(fieldname, label, bank_account)

            linked_gl_account = get_bank_account_gl_account(bank_account)

            if (
                fieldname == "default_business_bank_account"
                and linked_gl_account
                and not self.default_business_bank_gl_account
            ):
                self.default_business_bank_gl_account = linked_gl_account

            if (
                fieldname == "default_trust_account"
                and linked_gl_account
                and not self.default_trust_bank_gl_account
            ):
                self.default_trust_bank_gl_account = linked_gl_account

    def validate_bank_account_company(self, fieldname, label, bank_account):
        if not frappe.db.exists("Bank Account", bank_account):
            frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(bank_account)))

        meta = frappe.get_meta("Bank Account")
        if meta.has_field("company"):
            company = frappe.db.get_value("Bank Account", bank_account, "company")
            if company and company != self.default_company:
                frappe.throw(
                    _("{0} must belong to Default Company {1}. Current company: {2}").format(
                        label,
                        frappe.bold(self.default_company),
                        frappe.bold(company),
                    )
                )

    def validate_gl_accounts(self):
        account_fields = {
            "default_business_bank_gl_account": _("Default Business Bank GL Account"),
            "default_trust_bank_gl_account": _("Default Trust Bank GL Account"),
            "default_trust_creditor_account": _("Default Trust Creditor Account"),
            "default_trust_investment_account": _("Default Trust Investment Account"),
            "trust_interest_payable_account": _("Trust Interest Payable Account"),
            "trust_bank_charges_account": _("Trust Bank Charges Account"),
            "trust_rounding_difference_account": _("Trust Rounding Difference Account"),
            "default_receivable_account": _("Default Receivable Account"),
            "default_professional_fees_income_account": _("Default Professional Fees Income Account"),
            "default_disbursement_recovery_account": _("Default Disbursement Recovery Account"),
            "default_write_off_account": _("Default Write-Off Account"),
            "default_vat_output_account": _("Default VAT Output Account"),
            "default_vat_input_account": _("Default VAT Input Account"),
            "default_disbursement_expense_account": _("Default Disbursement Expense Account"),
            "default_recoverable_disbursement_account": _("Default Recoverable Disbursement Account"),
        }

        for fieldname, label in account_fields.items():
            account = self.get(fieldname)
            if not account:
                continue

            self.validate_account_company(fieldname, label, account)

        self.validate_bank_gl_account(
            "default_business_bank_gl_account",
            _("Default Business Bank GL Account"),
        )
        self.validate_bank_gl_account(
            "default_trust_bank_gl_account",
            _("Default Trust Bank GL Account"),
        )
        self.validate_trust_creditor_account()

    def validate_account_company(self, fieldname, label, account):
        if not frappe.db.exists("Account", account):
            frappe.throw(_("{0} {1} does not exist.").format(label, frappe.bold(account)))

        account_doc = frappe.db.get_value(
            "Account",
            account,
            ["company", "is_group", "disabled"],
            as_dict=True,
        )

        if account_doc.company != self.default_company:
            frappe.throw(
                _("{0} must belong to Default Company {1}. Current company: {2}").format(
                    label,
                    frappe.bold(self.default_company),
                    frappe.bold(account_doc.company),
                )
            )

        if cint(account_doc.is_group):
            frappe.throw(_("{0} must not be a group account: {1}").format(label, frappe.bold(account)))

        if cint(account_doc.disabled):
            frappe.throw(_("{0} is disabled: {1}").format(label, frappe.bold(account)))

    def validate_bank_gl_account(self, fieldname, label):
        account = self.get(fieldname)
        if not account:
            return

        details = frappe.db.get_value(
            "Account",
            account,
            ["account_type", "root_type"],
            as_dict=True,
        )
        if not details:
            return

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

    def validate_trust_creditor_account(self):
        account = self.default_trust_creditor_account
        if not account:
            return

        details = frappe.db.get_value(
            "Account",
            account,
            ["account_type", "root_type"],
            as_dict=True,
        )
        if not details:
            return

        if details.account_type in {"Bank", "Cash"}:
            frappe.throw(_("Default Trust Creditor Account must not be a Bank or Cash account."))

        if cint(self.strict_validation_mode) and details.root_type != "Liability":
            frappe.throw(
                _("Default Trust Creditor Account should be a Liability account in Strict Validation Mode. Current root type: {0}").format(
                    details.root_type or "Not Set"
                )
            )

    def validate_tax_templates(self):
        template_fields = {
            "default_sales_taxes_and_charges_template": "Sales Taxes and Charges Template",
            "default_purchase_taxes_and_charges_template": "Purchase Taxes and Charges Template",
        }

        for fieldname, doctype in template_fields.items():
            value = self.get(fieldname)
            if not value or not frappe.db.exists(doctype, value):
                continue

            meta = frappe.get_meta(doctype)
            if meta.has_field("company"):
                company = frappe.db.get_value(doctype, value, "company")
                if company and company != self.default_company:
                    frappe.throw(_("{0} must belong to Default Company {1}.").format(value, self.default_company))

    def validate_approval_consistency(self):
        if cint(self.require_trust_approval):
            required = {
                "require_approval_for_trust_payments": _("Require Approval for Trust Payments"),
                "require_approval_for_trust_transfer": _("Require Approval for Trust Transfer"),
                "trust_correction_requires_approval": _("Trust Correction Requires Approval"),
            }

            for fieldname, label in required.items():
                if not cint(self.get(fieldname)):
                    frappe.throw(_("{0} must be enabled when Require Trust Approval is enabled.").format(label))

        if cint(self.require_dual_approval_for_trust_payments) and flt(self.dual_approval_threshold) < 0:
            frappe.throw(_("Dual Approval Threshold cannot be negative."))

        if cint(self.enable_trust_to_business_transfers):
            recommended_required = {
                "require_invoice_for_trust_transfer": _("Require Invoice for Trust Transfer"),
                "prevent_transfer_above_invoice_outstanding": _("Prevent Transfer Above Invoice Outstanding"),
                "prevent_transfer_above_matter_trust_balance": _("Prevent Transfer Above Matter Trust Balance"),
                "require_approval_for_trust_transfer": _("Require Approval for Trust Transfer"),
            }

            for fieldname, label in recommended_required.items():
                if cint(self.strict_validation_mode) and not cint(self.get(fieldname)):
                    frappe.throw(
                        _("{0} must be enabled for Trust-to-Business Transfers in Strict Validation Mode.").format(label)
                    )

    def validate_reconciliation_settings(self):
        if not cint(self.require_monthly_trust_reconciliation):
            return

        if not self.trust_reconciliation_frequency:
            frappe.throw(_("Trust Reconciliation Frequency is required."))

        if cint(self.trust_reconciliation_due_day) < 1 or cint(self.trust_reconciliation_due_day) > 31:
            frappe.throw(_("Trust Reconciliation Due Day must be between 1 and 31."))

        if cint(self.require_review_of_trust_reconciliation) and not self.trust_reconciliation_reviewer_role:
            frappe.throw(_("Trust Reconciliation Reviewer Role is required when reconciliation review is required."))

        if flt(self.reconciliation_difference_tolerance) < 0:
            frappe.throw(_("Reconciliation Difference Tolerance cannot be negative."))

    def validate_billing_and_time_settings(self):
        if cint(self.enable_time_billing) and cint(self.default_time_billing_increment_minutes) <= 0:
            frappe.throw(_("Default Time Billing Increment Minutes must be greater than zero."))

        if cint(self.require_partner_approval_for_invoices) and not self.invoice_approval_role:
            frappe.throw(_("Invoice Approval Role is required when Partner Approval for Invoices is enabled."))


def is_hrms_installed():
    installed_apps = set(frappe.get_installed_apps())
    if "hrms" in installed_apps:
        return True

    # Some installations may still expose HR module metadata even if app naming differs.
    return bool(frappe.db.exists("Module Def", "HR"))


def get_bank_account_gl_account(bank_account):
    if not bank_account or not frappe.db.exists("Bank Account", bank_account):
        return None

    meta = frappe.get_meta("Bank Account")
    for fieldname in ("account", "gl_account"):
        if meta.has_field(fieldname):
            return frappe.db.get_value("Bank Account", bank_account, fieldname)

    return None
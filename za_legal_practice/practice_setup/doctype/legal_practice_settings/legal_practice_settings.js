// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Practice Settings", {
    refresh(frm) {
        set_queries(frm);
        refresh_runtime_flags(frm);
        apply_visibility_and_requirements(frm);
        add_settings_actions(frm);
    },

    default_company(frm) {
        clear_company_scoped_fields(frm);
        set_queries(frm);
    },

    enable_trust_accounting(frm) {
        apply_visibility_and_requirements(frm);
    },

    trust_account_model(frm) {
        apply_visibility_and_requirements(frm);
    },

    require_trust_approval(frm) {
        apply_trust_approval_defaults(frm);
        apply_visibility_and_requirements(frm);
    },

    enable_trust_to_business_transfers(frm) {
        apply_visibility_and_requirements(frm);
    },

    require_monthly_trust_reconciliation(frm) {
        apply_visibility_and_requirements(frm);
    },

    attorney_master_source(frm) {
        validate_attorney_master_source(frm);
    },

    enable_optional_employee_link(frm) {
        validate_optional_employee_link(frm);
    },

    default_business_bank_account(frm) {
        fetch_bank_account_gl_account(frm, "default_business_bank_account", "default_business_bank_gl_account");
    },

    default_trust_account(frm) {
        fetch_bank_account_gl_account(frm, "default_trust_account", "default_trust_bank_gl_account");
    }
});

function set_queries(frm) {
    const company = () => frm.doc.default_company;

    frm.set_query("default_business_bank_account", () => {
        return { filters: { company: company() } };
    });

    frm.set_query("default_trust_account", () => {
        return { filters: { company: company() } };
    });

    const account_fields = [
        "default_business_bank_gl_account",
        "default_trust_bank_gl_account",
        "default_trust_creditor_account",
        "default_trust_investment_account",
        "trust_interest_payable_account",
        "trust_bank_charges_account",
        "trust_rounding_difference_account",
        "default_receivable_account",
        "default_professional_fees_income_account",
        "default_disbursement_recovery_account",
        "default_write_off_account",
        "default_vat_output_account",
        "default_vat_input_account",
        "default_disbursement_expense_account",
        "default_recoverable_disbursement_account"
    ];

    account_fields.forEach((fieldname) => {
        frm.set_query(fieldname, () => {
            return {
                filters: {
                    company: company(),
                    is_group: 0,
                    disabled: 0
                }
            };
        });
    });

    frm.set_query("default_trust_bank_gl_account", () => {
        return {
            filters: {
                company: company(),
                is_group: 0,
                disabled: 0,
                account_type: "Bank"
            }
        };
    });

    frm.set_query("default_business_bank_gl_account", () => {
        return {
            filters: {
                company: company(),
                is_group: 0,
                disabled: 0,
                account_type: "Bank"
            }
        };
    });

    frm.set_query("default_sales_taxes_and_charges_template", () => {
        return { filters: { company: company() } };
    });

    frm.set_query("default_purchase_taxes_and_charges_template", () => {
        return { filters: { company: company() } };
    });
}

function refresh_runtime_flags(frm) {
    if (frm.is_new()) return;

    frm.call("refresh_runtime_flags")
        .then((r) => {
            const flags = r.message || {};

            if (Object.prototype.hasOwnProperty.call(flags, "hrms_installed")) {
                frm.set_value("hrms_installed", flags.hrms_installed ? 1 : 0);
            }

            if (Object.prototype.hasOwnProperty.call(flags, "require_hrms")) {
                frm.set_value("require_hrms", flags.require_hrms ? 1 : 0);
            }

            validate_attorney_master_source(frm, true);
            validate_optional_employee_link(frm, true);
        })
        .catch(() => {
            // Do not block form loading if the server method is unavailable during development/migration.
        });
}

function apply_visibility_and_requirements(frm) {
    const trust_enabled = cint(frm.doc.enable_trust_accounting);
    const single_trust = frm.doc.trust_account_model === "Single Trust Account";
    const trust_approval = cint(frm.doc.require_trust_approval);
    const trust_transfer = cint(frm.doc.enable_trust_to_business_transfers);
    const reconciliation = cint(frm.doc.require_monthly_trust_reconciliation);
    const client_portal = cint(frm.doc.enable_client_portal);
    const publishing = cint(frm.doc.enable_legal_publishing);
    const acts = cint(frm.doc.enable_acts_register);

    const trust_fields = [
        "trust_account_model",
        "default_trust_account",
        "default_trust_bank_gl_account",
        "require_trust_account_on_matter",
        "allow_multiple_trust_accounts_per_matter",
        "restrict_attorneys_by_trust_account",
        "default_trust_account_assignment_method",
        "default_trust_creditor_account",
        "default_trust_investment_account",
        "trust_interest_payable_account",
        "trust_bank_charges_account",
        "trust_rounding_difference_account",
        "allow_manual_gl_posting_to_trust_accounts"
    ];

    trust_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, trust_enabled);
    });

    frm.toggle_reqd("default_trust_account", trust_enabled && single_trust);
    frm.toggle_reqd("default_trust_creditor_account", trust_enabled);
    frm.toggle_reqd("trust_account_model", trust_enabled);

    const approval_fields = [
        "require_approval_for_trust_receipts",
        "require_approval_for_trust_payments",
        "require_dual_approval_for_trust_payments",
        "dual_approval_threshold",
        "require_supporting_document_for_trust_payment",
        "allow_trust_payment_without_matter",
        "prevent_negative_matter_trust_balance",
        "prevent_negative_trust_account_balance",
        "allow_overdrawn_trust_override",
        "require_beneficiary_verification",
        "require_payment_reference"
    ];

    approval_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, trust_enabled);
    });

    const correction_fields = [
        "allow_trust_corrections",
        "trust_correction_requires_reason",
        "trust_correction_requires_approval"
    ];

    correction_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, trust_enabled);
    });

    if (trust_approval) {
        frm.toggle_reqd("require_approval_for_trust_payments", true);
        frm.toggle_reqd("require_approval_for_trust_transfer", true);
        frm.toggle_reqd("trust_correction_requires_approval", true);
    }

    const transfer_fields = [
        "require_invoice_for_trust_transfer",
        "allow_transfer_against_draft_invoice",
        "prevent_transfer_above_invoice_outstanding",
        "prevent_transfer_above_matter_trust_balance",
        "require_approval_for_trust_transfer",
        "trust_transfer_approval_role",
        "auto_allocate_transfer_to_invoice",
        "trust_transfer_payment_mode"
    ];

    transfer_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, trust_enabled && trust_transfer);
    });

    frm.toggle_reqd(
        "trust_transfer_approval_role",
        trust_enabled && trust_transfer && cint(frm.doc.require_approval_for_trust_transfer)
    );

    const reconciliation_fields = [
        "trust_reconciliation_frequency",
        "trust_reconciliation_due_day",
        "require_review_of_trust_reconciliation",
        "trust_reconciliation_reviewer_role",
        "allow_reconciliation_with_difference",
        "reconciliation_difference_tolerance",
        "allow_reconciliation_override"
    ];

    reconciliation_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, trust_enabled && reconciliation);
    });

    frm.toggle_reqd(
        "trust_reconciliation_reviewer_role",
        trust_enabled && reconciliation && cint(frm.doc.require_review_of_trust_reconciliation)
    );

    [
        "portal_show_matter_status",
        "portal_show_documents",
        "portal_show_invoices",
        "portal_show_trust_balance"
    ].forEach((fieldname) => {
        frm.toggle_display(fieldname, client_portal);
    });

    [
        "enable_acts_register",
        "default_act_workflow",
        "publish_acts_to_website",
        "acts_route_prefix",
        "legal_blog_category"
    ].forEach((fieldname) => {
        frm.toggle_display(fieldname, publishing || cint(frm.doc.enable_acts_module_future));
    });

    ["publish_acts_to_website", "acts_route_prefix"].forEach((fieldname) => {
        frm.toggle_display(fieldname, acts);
    });
}

function apply_trust_approval_defaults(frm) {
    if (!cint(frm.doc.require_trust_approval)) return;

    const defaults = {
        require_approval_for_trust_payments: 1,
        require_approval_for_trust_transfer: 1,
        trust_correction_requires_approval: 1
    };

    Object.keys(defaults).forEach((fieldname) => {
        if (!cint(frm.doc[fieldname])) {
            frm.set_value(fieldname, defaults[fieldname]);
        }
    });
}

function validate_attorney_master_source(frm, silent) {
    if (frm.doc.attorney_master_source !== "Employee via HRMS") return;

    if (!cint(frm.doc.hrms_installed)) {
        frm.set_value("attorney_master_source", "Attorney Profile");

        if (!silent) {
            frappe.msgprint({
                title: __("HRMS Not Installed"),
                message: __(
                    "Employee via HRMS cannot be selected because HRMS/Frappe HR is not installed. Attorney Master Source was reset to Attorney Profile."
                ),
                indicator: "orange"
            });
        }
    }
}

function validate_optional_employee_link(frm, silent) {
    if (!cint(frm.doc.enable_optional_employee_link)) return;

    if (!cint(frm.doc.hrms_installed)) {
        frm.set_value("enable_optional_employee_link", 0);

        if (!silent) {
            frappe.msgprint({
                title: __("HRMS Not Installed"),
                message: __("Optional Employee Link was disabled because HRMS/Frappe HR is not installed."),
                indicator: "orange"
            });
        }
    }
}

function fetch_bank_account_gl_account(frm, bank_account_field, target_account_field) {
    const bank_account = frm.doc[bank_account_field];

    if (!bank_account || frm.doc[target_account_field]) return;

    frappe.db.get_value("Bank Account", bank_account, ["account", "company"])
        .then((r) => {
            const values = r.message || {};

            if (values.company && frm.doc.default_company && values.company !== frm.doc.default_company) {
                frappe.msgprint({
                    title: __("Company Mismatch"),
                    message: __(
                        `${frm.fields_dict[bank_account_field].df.label} belongs to ${values.company}, not ${frm.doc.default_company}.`
                    ),
                    indicator: "red"
                });
            }

            if (values.account && !frm.doc[target_account_field]) {
                frm.set_value(target_account_field, values.account);
            }
        });
}

function clear_company_scoped_fields(frm) {
    const fields = [
        "default_business_bank_account",
        "default_business_bank_gl_account",
        "default_trust_account",
        "default_trust_bank_gl_account",
        "default_trust_creditor_account",
        "default_trust_investment_account",
        "trust_interest_payable_account",
        "trust_bank_charges_account",
        "trust_rounding_difference_account",
        "default_receivable_account",
        "default_professional_fees_income_account",
        "default_disbursement_recovery_account",
        "default_write_off_account",
        "default_vat_output_account",
        "default_vat_input_account",
        "default_disbursement_expense_account",
        "default_recoverable_disbursement_account",
        "default_sales_taxes_and_charges_template",
        "default_purchase_taxes_and_charges_template"
    ];

    if (frm.is_new()) return;

    frappe.confirm(
        __("Changing Default Company can invalidate linked accounts and tax templates. Clear company-specific fields now?"),
        () => fields.forEach((fieldname) => frm.set_value(fieldname, null)),
        () => {}
    );
}

function add_settings_actions(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Refresh Runtime Flags"),
        () => refresh_runtime_flags(frm),
        __("Actions")
    );

    frm.add_custom_button(
        __("Apply Trust Approval Defaults"),
        () => apply_trust_approval_defaults(frm),
        __("Actions")
    );
}
// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Matter Type", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    matter_type_name(frm) {
        set_matter_type_code_if_missing(frm);
    },

    matter_type_code(frm) {
        normalize_code_field(frm, "matter_type_code");
    },

    matter_number_prefix(frm) {
        normalize_code_field(frm, "matter_number_prefix");
    },

    practice_area(frm) {
        fetch_practice_area_defaults(frm);
    },

    practice_branch(frm) {
        fetch_practice_branch_defaults(frm);
    },

    default_trust_account(frm) {
        fetch_bank_account_gl_account(frm);
    },

    trust_handling(frm) {
        apply_trust_handling_defaults(frm);
        apply_visibility_and_requirements(frm);
    },

    require_trust_account_on_matter(frm) {
        apply_visibility_and_requirements(frm);
    },

    billing_model(frm) {
        apply_visibility_and_requirements(frm);
    },

    status(frm) {
        if (frm.doc.status === "Archived") {
            frm.set_value("disabled", 1);
        }

        if (frm.doc.status === "Active" && cint(frm.doc.disabled)) {
            frm.set_value("disabled", 0);
        }
    },

    disabled(frm) {
        if (cint(frm.doc.disabled) && frm.doc.status === "Active") {
            frm.set_value("status", "Inactive");
        }
    }
});

function set_queries(frm) {
    frm.set_query("practice_area", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0,
                is_group: 0
            }
        };
    });

    frm.set_query("practice_branch", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
    });

    frm.set_query("default_matter_workflow", () => {
        return {
            filters: {
                document_type: "Matter",
                is_active: 1
            }
        };
    });

    frm.set_query("default_trust_bank_gl_account", () => {
        return {
            filters: {
                account_type: "Bank",
                root_type: "Asset",
                is_group: 0,
                disabled: 0
            }
        };
    });

    frm.set_query("default_trust_creditor_account", () => {
        return {
            filters: {
                root_type: "Liability",
                is_group: 0,
                disabled: 0
            }
        };
    });

    frm.set_query("default_income_account", () => {
        return {
            filters: {
                root_type: "Income",
                is_group: 0,
                disabled: 0
            }
        };
    });

    frm.set_query("default_disbursement_recovery_account", () => {
        return {
            filters: {
                is_group: 0,
                disabled: 0
            }
        };
    });

    ["default_hourly_rate_item", "default_consultation_item", "default_disbursement_item"].forEach((fieldname) => {
        frm.set_query(fieldname, () => {
            return {
                filters: {
                    disabled: 0
                }
            };
        });
    });

    frm.set_query("item", "billing_items", () => {
        return {
            filters: {
                disabled: 0
            }
        };
    });
}

function apply_visibility_and_requirements(frm) {
    const trust_not_applicable = frm.doc.trust_handling === "Not Applicable";
    const trust_required = frm.doc.trust_handling === "Required";
    const no_charge = frm.doc.billing_model === "No Charge";

    const trust_fields = [
        "default_trust_account",
        "default_trust_bank_gl_account",
        "default_trust_creditor_account",
        "require_trust_account_on_matter",
        "allow_trust_receipts",
        "allow_trust_payments",
        "allow_trust_to_business_transfers"
    ];

    trust_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, !trust_not_applicable);
    });

    frm.toggle_reqd("default_trust_account", trust_required || cint(frm.doc.require_trust_account_on_matter));

    const billing_fields = [
        "default_hourly_rate_item",
        "default_consultation_item",
        "default_disbursement_item",
        "default_income_account",
        "default_disbursement_recovery_account",
        "default_sales_taxes_and_charges_template",
        "require_partner_approval_for_billing",
        "billing_items"
    ];

    billing_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, !no_charge);
    });

    frm.toggle_display("default_stage", cint(frm.doc.enable_stage_tracking));
}

function apply_trust_handling_defaults(frm) {
    if (frm.doc.trust_handling === "Not Applicable") {
        frm.set_value("require_trust_account_on_matter", 0);
        frm.set_value("allow_trust_receipts", 0);
        frm.set_value("allow_trust_payments", 0);
        frm.set_value("allow_trust_to_business_transfers", 0);
    }

    if (frm.doc.trust_handling === "Required") {
        frm.set_value("require_trust_account_on_matter", 1);
        frm.set_value("allow_trust_receipts", 1);
        frm.set_value("allow_trust_payments", 1);
    }

    if (frm.doc.trust_handling === "Allowed") {
        frm.set_value("allow_trust_receipts", 1);
        frm.set_value("allow_trust_payments", 1);
    }
}

function set_matter_type_code_if_missing(frm) {
    if (!frm.doc.matter_type_name || frm.doc.matter_type_code) return;

    const code = make_code(frm.doc.matter_type_name);
    frm.set_value("matter_type_code", code);

    if (!frm.doc.matter_number_prefix) {
        frm.set_value("matter_number_prefix", code);
    }
}

function normalize_code_field(frm, fieldname) {
    if (!frm.doc[fieldname]) return;

    const code = make_code(frm.doc[fieldname]);

    if (frm.doc[fieldname] !== code) {
        frm.set_value(fieldname, code);
    }

    if (fieldname === "matter_type_code" && !frm.doc.matter_number_prefix) {
        frm.set_value("matter_number_prefix", code);
    }
}

function make_code(value) {
    return (value || "")
        .trim()
        .toUpperCase()
        .replace(/[^A-Z0-9]+/g, "_")
        .replace(/_+/g, "_")
        .replace(/^_+|_+$/g, "");
}

function fetch_bank_account_gl_account(frm) {
    if (!frm.doc.default_trust_account) {
        frm.set_value("default_trust_bank_gl_account", null);
        return;
    }

    frappe.db.get_value("Bank Account", frm.doc.default_trust_account, ["account", "company"])
        .then((r) => {
            const values = r.message || {};

            if (values.account) {
                frm.set_value("default_trust_bank_gl_account", values.account);
            }

            validate_bank_account_company(frm, values.company);
        });
}

function validate_bank_account_company(frm, bank_account_company) {
    if (!bank_account_company) return;

    frappe.db.get_single_value("Legal Practice Settings", "default_company")
        .then((default_company) => {
            if (default_company && default_company !== bank_account_company) {
                frappe.msgprint({
                    title: __("Company Mismatch"),
                    message: __(
                        `The selected Trust Account belongs to ${bank_account_company}, but Legal Practice Settings uses ${default_company}.`
                    ),
                    indicator: "red"
                });
            }
        });
}

function fetch_practice_area_defaults(frm) {
    if (!frm.doc.practice_area) return;

    frappe.db.get_value(
        "Practice Area",
        frm.doc.practice_area,
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
            "enable_estates_fields"
        ]
    ).then((r) => {
        const values = r.message || {};

        copy_if_empty(frm, "matter_number_prefix", values.matter_number_prefix);
        copy_if_empty(frm, "default_matter_status", values.default_matter_status);
        copy_if_empty(frm, "default_matter_workflow", values.default_matter_workflow);
        copy_if_empty(frm, "default_trust_account", values.default_trust_account);
        copy_if_empty(frm, "default_trust_creditor_account", values.default_trust_creditor_account);
        copy_if_empty(frm, "default_income_account", values.default_income_account);
        copy_if_empty(frm, "default_disbursement_recovery_account", values.default_disbursement_recovery_account);
        copy_if_empty(frm, "default_sales_taxes_and_charges_template", values.default_sales_taxes_and_charges_template);

        ["require_conflict_check", "require_fica", "require_mandate"].forEach((fieldname) => {
            if (Object.prototype.hasOwnProperty.call(values, fieldname)) {
                frm.set_value(fieldname, values[fieldname] ? 1 : 0);
            }
        });

        [
            "enable_litigation_fields",
            "enable_conveyancing_fields",
            "enable_collections_fields",
            "enable_estates_fields"
        ].forEach((fieldname) => {
            if (values[fieldname]) {
                frm.set_value(fieldname, 1);
            }
        });
    });
}

function fetch_practice_branch_defaults(frm) {
    if (!frm.doc.practice_branch) return;

    frappe.db.get_value(
        "Practice Branch",
        frm.doc.practice_branch,
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
            "matter_closing_approval_role",
            "invoice_approval_role"
        ]
    ).then((r) => {
        const values = r.message || {};

        copy_if_empty(frm, "matter_number_prefix", values.matter_number_prefix);
        copy_if_empty(frm, "default_matter_status", values.default_matter_status);
        copy_if_empty(frm, "default_matter_workflow", values.default_matter_workflow);
        copy_if_empty(frm, "default_trust_account", values.default_trust_account);
        copy_if_empty(frm, "default_trust_creditor_account", values.default_trust_creditor_account);
        copy_if_empty(frm, "default_income_account", values.default_income_account);
        copy_if_empty(frm, "default_disbursement_recovery_account", values.default_disbursement_recovery_account);
        copy_if_empty(frm, "default_sales_taxes_and_charges_template", values.default_sales_taxes_and_charges_template);
        copy_if_empty(frm, "matter_closing_approval_role", values.matter_closing_approval_role);

        ["require_conflict_check", "require_fica", "require_mandate"].forEach((fieldname) => {
            if (Object.prototype.hasOwnProperty.call(values, fieldname)) {
                frm.set_value(fieldname, values[fieldname] ? 1 : 0);
            }
        });
    });
}

function copy_if_empty(frm, fieldname, value) {
    if (!value || frm.doc[fieldname]) return;
    frm.set_value(fieldname, value);
}

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Create Matter"),
        () => {
            frappe.new_doc("Matter", {
                matter_type: frm.doc.name,
                practice_area: frm.doc.practice_area,
                practice_branch: frm.doc.practice_branch
            });
        },
        __("Actions")
    );
}
// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Practice Branch", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    branch_name(frm) {
        set_branch_code_if_missing(frm);
    },

    branch_code(frm) {
        normalize_code_field(frm, "branch_code");
    },

    matter_number_prefix(frm) {
        normalize_code_field(frm, "matter_number_prefix");
    },

    default_business_bank_account(frm) {
        fetch_bank_account_gl_account(frm, "default_business_bank_account", "default_business_bank_gl_account");
    },

    default_trust_account(frm) {
        fetch_bank_account_gl_account(frm, "default_trust_account", "default_trust_bank_gl_account");
    },

    require_trust_account_on_matter(frm) {
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
    frm.set_query("branch_manager", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
    });

    frm.set_query("responsible_partner", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0,
                attorney_type: ["in", ["Partner", "Director"]]
            }
        };
    });

    frm.set_query("default_attorney", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
    });

    frm.set_query("default_practice_area", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0,
                is_group: 0
            }
        };
    });

    frm.set_query("default_cost_center", () => {
        return {
            filters: {
                is_group: 0
            }
        };
    });

    frm.set_query("default_business_bank_gl_account", () => {
        return {
            filters: {
                account_type: "Bank",
                root_type: "Asset",
                is_group: 0,
                disabled: 0
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

    frm.set_query("default_receivable_account", () => {
        return {
            filters: {
                root_type: "Asset",
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

    frm.set_query("default_write_off_account", () => {
        return {
            filters: {
                is_group: 0,
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
}

function apply_visibility_and_requirements(frm) {
    const require_trust_account = cint(frm.doc.require_trust_account_on_matter);

    frm.toggle_reqd("default_trust_account", require_trust_account);
    frm.toggle_reqd("default_trust_creditor_account", false);
    frm.toggle_reqd("default_business_bank_account", false);
}

function set_branch_code_if_missing(frm) {
    if (!frm.doc.branch_name || frm.doc.branch_code) return;

    const code = make_code(frm.doc.branch_name);
    frm.set_value("branch_code", code);

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

    if (fieldname === "branch_code" && !frm.doc.matter_number_prefix) {
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

function fetch_bank_account_gl_account(frm, bank_account_field, target_account_field) {
    const bank_account = frm.doc[bank_account_field];

    if (!bank_account) {
        frm.set_value(target_account_field, null);
        return;
    }

    frappe.db.get_value("Bank Account", bank_account, ["account", "company"])
        .then((r) => {
            const values = r.message || {};

            if (values.account) {
                frm.set_value(target_account_field, values.account);
            }

            validate_bank_account_company(frm, values.company, bank_account);
        });
}

function validate_bank_account_company(frm, bank_account_company, bank_account) {
    if (!bank_account_company) return;

    frappe.db.get_single_value("Legal Practice Settings", "default_company")
        .then((default_company) => {
            if (default_company && default_company !== bank_account_company) {
                frappe.msgprint({
                    title: __("Company Mismatch"),
                    message: __(
                        `Bank Account ${bank_account} belongs to ${bank_account_company}, but Legal Practice Settings uses ${default_company}.`
                    ),
                    indicator: "red"
                });
            }
        });
}

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    if (frm.doc.erpnext_branch) {
        frm.add_custom_button(
            __("Open ERPNext Branch"),
            () => {
                frappe.set_route("Form", "Branch", frm.doc.erpnext_branch);
            },
            __("Actions")
        );
    }

    frm.add_custom_button(
        __("Create Practice Area"),
        () => {
            frappe.new_doc("Practice Area", {
                default_branch: frm.doc.erpnext_branch,
                default_cost_center: frm.doc.default_cost_center,
                default_trust_account: frm.doc.default_trust_account,
                default_trust_creditor_account: frm.doc.default_trust_creditor_account
            });
        },
        __("Actions")
    );
}
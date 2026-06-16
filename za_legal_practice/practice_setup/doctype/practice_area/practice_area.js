// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Practice Area", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    practice_area_name(frm) {
        set_area_code_if_missing(frm);
    },

    area_code(frm) {
        normalize_code_field(frm, "area_code");
    },

    matter_number_prefix(frm) {
        normalize_code_field(frm, "matter_number_prefix");
    },

    default_trust_account(frm) {
        fetch_bank_account_gl_account(frm);
    },

    require_trust_account_on_matter(frm) {
        apply_visibility_and_requirements(frm);
    },

    is_group(frm) {
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
    frm.set_query("parent_practice_area", () => {
        return {
            filters: {
                name: ["!=", frm.doc.name || ""],
                disabled: 0,
                status: "Active",
                is_group: 1
            }
        };
    });

    frm.set_query("responsible_attorney", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
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

    frm.set_query("default_sales_taxes_and_charges_template", () => {
        return {};
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
    const is_group = cint(frm.doc.is_group);
    const require_trust_account = cint(frm.doc.require_trust_account_on_matter);

    const transaction_default_fields = [
        "default_trust_account",
        "default_trust_bank_gl_account",
        "default_trust_creditor_account",
        "allow_trust_receipts",
        "allow_trust_payments",
        "allow_trust_to_business_transfers",
        "default_hourly_rate_item",
        "default_consultation_item",
        "default_disbursement_item",
        "default_income_account",
        "default_disbursement_recovery_account",
        "default_sales_taxes_and_charges_template"
    ];

    transaction_default_fields.forEach((fieldname) => {
        frm.toggle_display(fieldname, !is_group);
    });

    frm.toggle_reqd("default_trust_account", !is_group && require_trust_account);
    frm.toggle_reqd("default_trust_creditor_account", false);

    if (is_group) {
        frm.set_value("require_trust_account_on_matter", 0);
    }
}

function set_area_code_if_missing(frm) {
    if (!frm.doc.practice_area_name || frm.doc.area_code) return;

    const code = make_code(frm.doc.practice_area_name);
    frm.set_value("area_code", code);

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

    if (fieldname === "area_code" && !frm.doc.matter_number_prefix) {
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

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Create Child Practice Area"),
        () => {
            frappe.new_doc("Practice Area", {
                parent_practice_area: frm.doc.name
            });
        },
        __("Actions")
    );

    frm.add_custom_button(
        __("Open Tree"),
        () => {
            frappe.set_route("Tree", "Practice Area");
        },
        __("Actions")
    );
}
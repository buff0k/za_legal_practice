// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attorney Profile", {
    refresh(frm) {
        set_queries(frm);
        refresh_runtime_flags(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    user(frm) {
        set_user_details(frm);
    },

    attorney_type(frm) {
        apply_attorney_type_defaults(frm);
        apply_visibility_and_requirements(frm);
    },

    enable_optional_employee_link(frm) {
        validate_optional_employee_link(frm);
        apply_visibility_and_requirements(frm);
    },

    employee(frm) {
        validate_employee_user_match(frm);
    },

    enforce_trust_account_restrictions(frm) {
        apply_visibility_and_requirements(frm);
    },

    default_trust_account(frm) {
        fetch_bank_account_gl_account(frm, "default_trust_account", "default_trust_bank_gl_account");
    },

    requires_supervision(frm) {
        apply_visibility_and_requirements(frm);
    }
});

frappe.ui.form.on("Attorney Trust Account Access", {
    trust_account(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!row.trust_account) return;

        frappe.db.get_value("Bank Account", row.trust_account, ["account", "company"])
            .then((r) => {
                const values = r.message || {};

                if (values.account) {
                    frappe.model.set_value(cdt, cdn, "trust_bank_gl_account", values.account);
                }

                if (values.company) {
                    validate_bank_account_company(frm, values.company, row.trust_account);
                }
            });
    },

    is_default(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (!cint(row.is_default)) return;

        (frm.doc.permitted_trust_accounts || []).forEach((other) => {
            if (other.name !== row.name && cint(other.is_default)) {
                frappe.model.set_value(other.doctype, other.name, "is_default", 0);
            }
        });

        if (row.trust_account) {
            frm.set_value("default_trust_account", row.trust_account);
            if (row.trust_bank_gl_account) {
                frm.set_value("default_trust_bank_gl_account", row.trust_bank_gl_account);
            }
        }
    }
});

function set_queries(frm) {
    frm.set_query("user", () => {
        return {
            filters: {
                enabled: 1
            }
        };
    });

    frm.set_query("employee", () => {
        return {};
    });

    frm.set_query("cost_center", () => {
        return {
            filters: {
                is_group: 0
            }
        };
    });

    frm.set_query("default_hourly_rate_item", () => {
        return {
            filters: {
                disabled: 0
            }
        };
    });

    frm.set_query("default_consultation_item", () => {
        return {
            filters: {
                disabled: 0
            }
        };
    });

    frm.set_query("default_trust_account", () => {
        return {};
    });

    frm.set_query("default_trust_bank_gl_account", () => {
        return {
            filters: {
                account_type: "Bank",
                is_group: 0,
                disabled: 0
            }
        };
    });

    frm.set_query("trust_account", "permitted_trust_accounts", () => {
        return {};
    });

    frm.set_query("trust_bank_gl_account", "permitted_trust_accounts", () => {
        return {
            filters: {
                account_type: "Bank",
                is_group: 0,
                disabled: 0
            }
        };
    });

    frm.set_query("supervising_attorney", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
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

            validate_optional_employee_link(frm, true);
            apply_visibility_and_requirements(frm);
        })
        .catch(() => {
            // Do not block form loading if the server method is unavailable during development/migration.
        });
}

function apply_visibility_and_requirements(frm) {
    const hrms_installed = cint(frm.doc.hrms_installed);
    const optional_employee_link = cint(frm.doc.enable_optional_employee_link);
    const trust_restrictions = cint(frm.doc.enforce_trust_account_restrictions);
    const requires_supervision = cint(frm.doc.requires_supervision);
    const is_candidate = frm.doc.attorney_type === "Candidate Attorney" || cint(frm.doc.is_candidate_attorney);

    frm.toggle_display("employee", hrms_installed && optional_employee_link);
    frm.toggle_reqd("employee", false);

    frm.toggle_display("permitted_trust_accounts", trust_restrictions);
    frm.toggle_display("default_trust_account", trust_restrictions);
    frm.toggle_display("default_trust_bank_gl_account", trust_restrictions);

    frm.toggle_reqd("default_trust_account", false);

    frm.toggle_display("supervising_attorney", requires_supervision || is_candidate);
    frm.toggle_reqd("supervising_attorney", requires_supervision);

    frm.toggle_display("admission_date", !is_candidate);
    frm.toggle_display("lpc_number", !is_candidate || cint(frm.doc.is_admitted_attorney));

    frm.toggle_display(
        "right_of_appearance_date",
        frm.doc.right_of_appearance && frm.doc.right_of_appearance !== "None"
    );
}

function apply_attorney_type_defaults(frm) {
    if (frm.doc.attorney_type === "Candidate Attorney") {
        frm.set_value("is_candidate_attorney", 1);
        frm.set_value("is_admitted_attorney", 0);
        frm.set_value("requires_supervision", 1);
    }

    if (["Attorney", "Partner", "Director", "Consultant"].includes(frm.doc.attorney_type)) {
        frm.set_value("is_candidate_attorney", 0);
        frm.set_value("is_admitted_attorney", 1);
    }

    if (["Partner", "Director"].includes(frm.doc.attorney_type)) {
        frm.set_value("can_close_matters", 1);
        frm.set_value("can_override_matter_controls", 1);
    }
}

function validate_optional_employee_link(frm, silent) {
    if (!cint(frm.doc.enable_optional_employee_link)) return;

    if (!cint(frm.doc.hrms_installed)) {
        frm.set_value("enable_optional_employee_link", 0);
        frm.set_value("employee", null);

        if (!silent) {
            frappe.msgprint({
                title: __("HRMS Not Installed"),
                message: __("Optional Employee Link was disabled because HRMS/Frappe HR is not installed."),
                indicator: "orange"
            });
        }
    }
}

function set_user_details(frm) {
    if (!frm.doc.user) return;

    frappe.db.get_value("User", frm.doc.user, ["full_name", "email", "mobile_no", "phone"])
        .then((r) => {
            const values = r.message || {};

            if (values.full_name && !frm.doc.attorney_name) {
                frm.set_value("attorney_name", values.full_name);
            }

            if (values.email) {
                frm.set_value("email", values.email);
            }

            if (values.mobile_no && !frm.doc.mobile_no) {
                frm.set_value("mobile_no", values.mobile_no);
            }

            if (values.phone && !frm.doc.phone) {
                frm.set_value("phone", values.phone);
            }
        });
}

function validate_employee_user_match(frm) {
    if (!frm.doc.employee || !frm.doc.user) return;

    frappe.db.get_value("Employee", frm.doc.employee, "user_id")
        .then((r) => {
            const user_id = r.message ? r.message.user_id : null;

            if (user_id && user_id !== frm.doc.user) {
                frappe.msgprint({
                    title: __("Employee/User Mismatch"),
                    message: __(
                        `Selected Employee is linked to User ${user_id}, but this Attorney Profile is linked to User ${frm.doc.user}.`
                    ),
                    indicator: "red"
                });
            }
        });
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

            if (values.company) {
                validate_bank_account_company(frm, values.company, bank_account);
            }
        });
}

function validate_bank_account_company(frm, bank_account_company, bank_account) {
    frappe.db.get_single_value("Legal Practice Settings", "default_company")
        .then((default_company) => {
            if (default_company && bank_account_company && default_company !== bank_account_company) {
                frappe.msgprint({
                    title: __("Trust Account Company Mismatch"),
                    message: __(
                        `Trust Account ${bank_account} belongs to ${bank_account_company}, but Legal Practice Settings uses ${default_company}.`
                    ),
                    indicator: "red"
                });
            }
        });
}

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Sync User Permissions"),
        () => {
            frm.call("sync_user_permissions").then((r) => {
                const result = r.message || {};
                if (result.synced) {
                    frappe.show_alert({
                        message: __("User Permissions synced. Created {0} new permission(s).", [result.created || 0]),
                        indicator: "green"
                    });
                } else {
                    frappe.show_alert({
                        message: __(result.reason || "No permissions synced."),
                        indicator: "orange"
                    });
                }
            });
        },
        __("Actions")
    );

    frm.add_custom_button(
        __("Refresh Runtime Flags"),
        () => refresh_runtime_flags(frm),
        __("Actions")
    );
}
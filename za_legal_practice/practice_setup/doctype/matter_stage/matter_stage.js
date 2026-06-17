// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Matter Stage", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    stage_name(frm) {
        set_stage_code_if_missing(frm);
    },

    stage_code(frm) {
        normalize_code_field(frm, "stage_code");
    },

    practice_area(frm) {
        if (frm.doc.matter_type) {
            validate_matter_type_practice_area(frm);
        }
    },

    applies_to_all_matter_types(frm) {
        if (cint(frm.doc.applies_to_all_matter_types)) {
            frm.set_value("matter_type", null);
        }

        apply_visibility_and_requirements(frm);
    },

    matter_type(frm) {
        if (frm.doc.matter_type) {
            frm.set_value("applies_to_all_matter_types", 0);
            fetch_matter_type_defaults(frm);
        }

        apply_visibility_and_requirements(frm);
    },

    is_initial_stage(frm) {
        if (cint(frm.doc.is_initial_stage)) {
            frm.set_value("is_default_stage", 1);
        }
    },

    is_closed_stage(frm) {
        if (cint(frm.doc.is_closed_stage)) {
            apply_closed_stage_defaults(frm);
        }
    },

    is_closing_stage(frm) {
        if (cint(frm.doc.is_closing_stage)) {
            apply_closing_stage_defaults(frm);
        }
    },

    prevent_trust_activity(frm) {
        if (cint(frm.doc.prevent_trust_activity)) {
            frm.set_value("allow_trust_receipts", 0);
            frm.set_value("allow_trust_payments", 0);
            frm.set_value("allow_trust_to_business_transfers", 0);
        }
    },

    require_partner_approval(frm) {
        apply_visibility_and_requirements(frm);
    },

    target_days(frm) {
        validate_warning_days(frm);
    },

    warning_days_before_target(frm) {
        validate_warning_days(frm);
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

    frm.set_query("matter_type", () => {
        const filters = {
            status: "Active",
            disabled: 0
        };

        if (frm.doc.practice_area) {
            filters.practice_area = frm.doc.practice_area;
        }

        return { filters };
    });

    frm.set_query("next_stage", () => {
        return get_stage_link_filters(frm);
    });

    frm.set_query("previous_stage", () => {
        return get_stage_link_filters(frm);
    });

    frm.set_query("approval_role", () => {
        return {
            filters: {
                disabled: 0
            }
        };
    });

    frm.set_query("escalation_role", () => {
        return {
            filters: {
                disabled: 0
            }
        };
    });
}

function get_stage_link_filters(frm) {
    const filters = {
        status: "Active",
        disabled: 0
    };

    if (!frm.is_new()) {
        filters.name = ["!=", frm.doc.name];
    }

    if (frm.doc.practice_area) {
        filters.practice_area = ["in", [frm.doc.practice_area, ""]];
    }

    return { filters };
}

function apply_visibility_and_requirements(frm) {
    const applies_to_all = cint(frm.doc.applies_to_all_matter_types);

    frm.toggle_display("matter_type", !applies_to_all);
    frm.toggle_reqd("matter_type", !applies_to_all);

    frm.toggle_display("approval_role", cint(frm.doc.require_partner_approval));
    frm.toggle_reqd("approval_role", cint(frm.doc.require_partner_approval));

    frm.toggle_display("warning_days_before_target", cint(frm.doc.target_days) > 0);
}

function set_stage_code_if_missing(frm) {
    if (!frm.doc.stage_name || frm.doc.stage_code) return;

    frm.set_value("stage_code", make_code(frm.doc.stage_name));
}

function normalize_code_field(frm, fieldname) {
    if (!frm.doc[fieldname]) return;

    const code = make_code(frm.doc[fieldname]);

    if (frm.doc[fieldname] !== code) {
        frm.set_value(fieldname, code);
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

function fetch_matter_type_defaults(frm) {
    if (!frm.doc.matter_type) return;

    frappe.db.get_value(
        "Matter Type",
        frm.doc.matter_type,
        [
            "practice_area",
            "enable_litigation_fields",
            "enable_conveyancing_fields",
            "enable_collections_fields",
            "enable_estates_fields"
        ]
    ).then((r) => {
        const values = r.message || {};

        if (values.practice_area && !frm.doc.practice_area) {
            frm.set_value("practice_area", values.practice_area);
        }

        if (values.practice_area && frm.doc.practice_area && values.practice_area !== frm.doc.practice_area) {
            frappe.msgprint({
                title: __("Practice Area Mismatch"),
                message: __(
                    `The selected Matter Type belongs to Practice Area ${values.practice_area}, not ${frm.doc.practice_area}.`
                ),
                indicator: "red"
            });
        }
    });
}

function validate_matter_type_practice_area(frm) {
    if (!frm.doc.matter_type || !frm.doc.practice_area) return;

    frappe.db.get_value("Matter Type", frm.doc.matter_type, "practice_area")
        .then((r) => {
            const matter_type_practice_area = r.message && r.message.practice_area;

            if (matter_type_practice_area && matter_type_practice_area !== frm.doc.practice_area) {
                frappe.msgprint({
                    title: __("Practice Area Mismatch"),
                    message: __(
                        `The selected Matter Type belongs to Practice Area ${matter_type_practice_area}, not ${frm.doc.practice_area}.`
                    ),
                    indicator: "red"
                });
            }
        });
}

function apply_closed_stage_defaults(frm) {
    frm.set_value("is_closing_stage", 1);

    frm.set_value("allow_trust_receipts", 0);
    frm.set_value("allow_trust_payments", 0);
    frm.set_value("allow_trust_to_business_transfers", 0);
    frm.set_value("prevent_trust_activity", 1);
    frm.set_value("require_trust_balance_zero", 1);

    frm.set_value("allow_time_entries", 0);
    frm.set_value("allow_disbursements", 0);
    frm.set_value("allow_billing", 0);

    frm.set_value("require_unbilled_time_clear", 1);
    frm.set_value("require_unbilled_disbursements_clear", 1);
    frm.set_value("require_open_tasks_complete", 1);
}

function apply_closing_stage_defaults(frm) {
    frm.set_value("require_required_documents_complete", 1);
    frm.set_value("require_open_tasks_complete", 1);
}

function validate_warning_days(frm) {
    const target_days = cint(frm.doc.target_days);
    const warning_days = cint(frm.doc.warning_days_before_target);

    if (target_days > 0 && warning_days > target_days) {
        frappe.msgprint({
            title: __("Invalid Warning Days"),
            message: __("Warning Days Before Target cannot be greater than Target Days."),
            indicator: "red"
        });

        frm.set_value("warning_days_before_target", target_days);
    }
}

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Create Similar Stage"),
        () => {
            frappe.new_doc("Matter Stage", {
                practice_area: frm.doc.practice_area,
                matter_type: frm.doc.matter_type,
                applies_to_all_matter_types: frm.doc.applies_to_all_matter_types,
                mapped_matter_status: frm.doc.mapped_matter_status,
                allow_trust_receipts: frm.doc.allow_trust_receipts,
                allow_trust_payments: frm.doc.allow_trust_payments,
                allow_trust_to_business_transfers: frm.doc.allow_trust_to_business_transfers,
                allow_time_entries: frm.doc.allow_time_entries,
                allow_disbursements: frm.doc.allow_disbursements,
                allow_billing: frm.doc.allow_billing
            });
        },
        __("Actions")
    );
}
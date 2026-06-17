// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Party Role", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    role_name(frm) {
        set_role_code_if_missing(frm);
    },

    role_code(frm) {
        normalize_code_field(frm, "role_code");
    },

    role_category(frm) {
        apply_category_defaults(frm);
        apply_visibility_and_requirements(frm);
    },

    party_side(frm) {
        apply_party_side_defaults(frm);
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

    requires_fica(frm) {
        if (cint(frm.doc.requires_fica)) {
            frm.set_value("include_in_fica_check", 1);
            frm.set_value("requires_id_or_registration_number", 1);
            frm.set_value("requires_address", 1);
        }
    },

    include_in_fica_check(frm) {
        if (cint(frm.doc.include_in_fica_check)) {
            frm.set_value("requires_fica", 1);
        }
    },

    requires_mandate(frm) {
        if (cint(frm.doc.requires_mandate)) {
            frm.set_value("can_be_client", 1);
            frm.set_value("party_side", "Client Side");
        }
    },

    is_primary_litigation_party(frm) {
        if (cint(frm.doc.is_primary_litigation_party)) {
            frm.set_value("role_category", "Litigation");
            frm.set_value("appears_on_court_documents", 1);
            frm.set_value("include_in_documents", 1);
        }
    },

    is_primary_conveyancing_party(frm) {
        if (cint(frm.doc.is_primary_conveyancing_party)) {
            frm.set_value("role_category", "Conveyancing");
            frm.set_value("include_in_documents", 1);
            frm.set_value("requires_address", 1);
        }
    },

    is_debtor_role(frm) {
        if (cint(frm.doc.is_debtor_role)) {
            frm.set_value("collections_role_type", "Debtor");
            frm.set_value("role_category", "Collections");
        }
    },

    is_creditor_role(frm) {
        if (cint(frm.doc.is_creditor_role)) {
            frm.set_value("collections_role_type", "Creditor");
            frm.set_value("role_category", "Collections");
        }
    },

    is_surety_role(frm) {
        if (cint(frm.doc.is_surety_role)) {
            frm.set_value("collections_role_type", "Surety");
            frm.set_value("role_category", "Collections");
        }
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
}

function apply_visibility_and_requirements(frm) {
    const applies_to_all = cint(frm.doc.applies_to_all_matter_types);

    frm.toggle_display("matter_type", !applies_to_all);
    frm.toggle_reqd("matter_type", !applies_to_all);

    const category = frm.doc.role_category;

    frm.toggle_display("litigation_section", category === "Litigation" || cint(frm.doc.is_primary_litigation_party));
    frm.toggle_display("conveyancing_section", category === "Conveyancing" || cint(frm.doc.is_primary_conveyancing_party));
    frm.toggle_display("collections_section", category === "Collections" || cint(frm.doc.is_debtor_role) || cint(frm.doc.is_creditor_role) || cint(frm.doc.is_surety_role));

    frm.toggle_reqd("litigation_role_type", category === "Litigation");
    frm.toggle_reqd("conveyancing_role_type", category === "Conveyancing");
    frm.toggle_reqd("collections_role_type", category === "Collections");
}

function set_role_code_if_missing(frm) {
    if (!frm.doc.role_name || frm.doc.role_code) return;

    frm.set_value("role_code", make_code(frm.doc.role_name));
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

function apply_category_defaults(frm) {
    const category = frm.doc.role_category;

    if (category === "Client") {
        frm.set_value("can_be_client", 1);
        frm.set_value("can_be_opposing_party", 0);
        frm.set_value("can_be_third_party", 0);
        frm.set_value("party_side", "Client Side");
        frm.set_value("include_in_conflict_check", 1);
        frm.set_value("include_in_fica_check", 1);
        frm.set_value("requires_fica", 1);
        frm.set_value("requires_mandate", 1);
        frm.set_value("requires_id_or_registration_number", 1);
        frm.set_value("requires_address", 1);
        frm.set_value("include_in_billing", 1);
    }

    if (category === "Opposing Party") {
        frm.set_value("can_be_client", 0);
        frm.set_value("can_be_opposing_party", 1);
        frm.set_value("can_be_third_party", 0);
        frm.set_value("party_side", "Opposing Side");
        frm.set_value("include_in_conflict_check", 1);
        frm.set_value("include_in_fica_check", 0);
        frm.set_value("requires_mandate", 0);
    }

    if (category === "Professional") {
        frm.set_value("can_be_professional_party", 1);
        frm.set_value("can_be_third_party", 1);
        frm.set_value("party_side", "Third Party");
        frm.set_value("requires_fica", 0);
        frm.set_value("requires_mandate", 0);
    }

    if (category === "Court / Forum") {
        frm.set_value("can_be_court_or_forum", 1);
        frm.set_value("can_be_third_party", 0);
        frm.set_value("party_side", "Court / Forum");
        frm.set_value("include_in_conflict_check", 0);
        frm.set_value("include_in_fica_check", 0);
        frm.set_value("requires_fica", 0);
        frm.set_value("requires_mandate", 0);
        frm.set_value("requires_contact_details", 1);
    }

    if (category === "State Entity") {
        frm.set_value("can_be_state_entity", 1);
        frm.set_value("party_side", "Third Party");
        frm.set_value("include_in_conflict_check", 1);
    }

    if (category === "Internal") {
        frm.set_value("can_be_internal_party", 1);
        frm.set_value("can_be_third_party", 0);
        frm.set_value("party_side", "Internal");
        frm.set_value("include_in_conflict_check", 0);
        frm.set_value("include_in_fica_check", 0);
        frm.set_value("requires_fica", 0);
        frm.set_value("requires_mandate", 0);
    }

    if (category === "Litigation") {
        frm.set_value("include_in_conflict_check", 1);
        frm.set_value("include_in_documents", 1);
        frm.set_value("appears_on_court_documents", 1);
    }

    if (category === "Conveyancing") {
        frm.set_value("include_in_conflict_check", 1);
        frm.set_value("include_in_documents", 1);
        frm.set_value("requires_address", 1);
    }

    if (category === "Collections") {
        frm.set_value("include_in_conflict_check", 1);
        frm.set_value("include_in_documents", 1);
    }
}

function apply_party_side_defaults(frm) {
    if (frm.doc.party_side === "Client Side") {
        frm.set_value("can_be_client", 1);
    }

    if (frm.doc.party_side === "Opposing Side") {
        frm.set_value("can_be_opposing_party", 1);
    }

    if (frm.doc.party_side === "Court / Forum") {
        frm.set_value("can_be_court_or_forum", 1);
    }

    if (frm.doc.party_side === "Internal") {
        frm.set_value("can_be_internal_party", 1);
    }
}

function fetch_matter_type_defaults(frm) {
    if (!frm.doc.matter_type) return;

    frappe.db.get_value(
        "Matter Type",
        frm.doc.matter_type,
        ["practice_area"]
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

function add_custom_buttons(frm) {
    if (frm.is_new()) return;

    frm.add_custom_button(
        __("Create Similar Role"),
        () => {
            frappe.new_doc("Legal Party Role", {
                role_category: frm.doc.role_category,
                party_side: frm.doc.party_side,
                practice_area: frm.doc.practice_area,
                matter_type: frm.doc.matter_type,
                applies_to_all_matter_types: frm.doc.applies_to_all_matter_types,
                can_be_client: frm.doc.can_be_client,
                can_be_opposing_party: frm.doc.can_be_opposing_party,
                can_be_third_party: frm.doc.can_be_third_party,
                can_be_professional_party: frm.doc.can_be_professional_party,
                can_be_court_or_forum: frm.doc.can_be_court_or_forum,
                can_be_state_entity: frm.doc.can_be_state_entity,
                can_be_internal_party: frm.doc.can_be_internal_party,
                include_in_conflict_check: frm.doc.include_in_conflict_check,
                include_in_fica_check: frm.doc.include_in_fica_check,
                include_in_documents: frm.doc.include_in_documents
            });
        },
        __("Actions")
    );
}
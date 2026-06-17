// Copyright (c) 2026, BuFf0k and contributors
// For license information, please see license.txt

frappe.ui.form.on("Legal Forum", {
    refresh(frm) {
        set_queries(frm);
        apply_visibility_and_requirements(frm);
        add_custom_buttons(frm);
    },

    forum_name(frm) {
        set_forum_code_if_missing(frm);
    },

    forum_code(frm) {
        normalize_code_field(frm, "forum_code");
    },

    forum_type(frm) {
        apply_forum_type_defaults(frm);
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

    practice_area(frm) {
        if (frm.doc.matter_type) {
            validate_matter_type_practice_area(frm);
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
    frm.set_query("default_party_role", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
    });

    frm.set_query("default_matter_stage", () => {
        return {
            filters: {
                status: "Active",
                disabled: 0
            }
        };
    });

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
}

function set_forum_code_if_missing(frm) {
    if (!frm.doc.forum_name || frm.doc.forum_code) return;

    frm.set_value("forum_code", make_code(frm.doc.forum_name));
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

function apply_forum_type_defaults(frm) {
    const forum_type = frm.doc.forum_type;

    const court_types = [
        "Constitutional Court",
        "Supreme Court of Appeal",
        "High Court",
        "Labour Court",
        "Labour Appeal Court",
        "Land Court",
        "Land Claims Court",
        "Electoral Court",
        "Tax Court",
        "Equality Court",
        "Small Claims Court",
        "Maintenance Court",
        "Children's Court",
        "Divorce Court",
        "Regional Magistrates Court",
        "District Magistrates Court"
    ];

    const tribunal_types = [
        "CCMA",
        "Bargaining Council",
        "Competition Tribunal",
        "Consumer Tribunal",
        "Companies Tribunal",
        "Tribunal"
    ];

    if (forum_type === "Constitutional Court") {
        frm.set_value("forum_level", "Apex Court");
        frm.set_value("jurisdiction_level", "National");
    } else if (["Supreme Court of Appeal", "Labour Appeal Court", "Competition Appeal Court"].includes(forum_type)) {
        frm.set_value("forum_level", "Appeal Court");
        frm.set_value("jurisdiction_level", "National");
    } else if (forum_type === "High Court") {
        frm.set_value("forum_level", "Superior Court");
    } else if (court_types.includes(forum_type)) {
        frm.set_value("forum_level", forum_type.includes("Magistrates") ? "Lower Court" : "Specialist Court");
    } else if (tribunal_types.includes(forum_type)) {
        frm.set_value("forum_level", "Commission / Tribunal");
    } else if (["Arbitration Forum", "Mediation Forum"].includes(forum_type)) {
        frm.set_value("forum_level", "Forum");
    }

    if (court_types.includes(forum_type)) {
        frm.set_value("appears_on_court_documents", 1);
    }

    if (!frm.doc.default_party_role) {
        frappe.db.exists("Legal Party Role", "COURT").then((exists) => {
            if (exists) {
                frm.set_value("default_party_role", "COURT");
            }
        });
    }
}

function fetch_matter_type_defaults(frm) {
    if (!frm.doc.matter_type) return;

    frappe.db.get_value("Matter Type", frm.doc.matter_type, ["practice_area"])
        .then((r) => {
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
        __("Create Similar Forum"),
        () => {
            frappe.new_doc("Legal Forum", {
                forum_type: frm.doc.forum_type,
                forum_level: frm.doc.forum_level,
                jurisdiction_level: frm.doc.jurisdiction_level,
                province: frm.doc.province,
                division: frm.doc.division,
                default_party_role: frm.doc.default_party_role,
                appears_on_court_documents: frm.doc.appears_on_court_documents,
                practice_area: frm.doc.practice_area,
                matter_type: frm.doc.matter_type,
                applies_to_all_matter_types: frm.doc.applies_to_all_matter_types
            });
        },
        __("Actions")
    );
}